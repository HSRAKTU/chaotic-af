"""Process supervisor for managing agent lifecycle.

Requirements:
- Start agents as separate processes
- Monitor process health
- Restart failed agents
- Graceful shutdown
- Process isolation for stability
"""

import asyncio
import subprocess
import sys
import json
import signal
from typing import Dict, Optional, List
from dataclasses import dataclass
from pathlib import Path
import psutil

from ..core.config import AgentConfig
from ..core.logging import AgentLogger
from .connection_manager import ConnectionManager


@dataclass
class AgentProcess:
    """Represents a running agent process."""
    config: AgentConfig
    process: Optional[subprocess.Popen] = None
    pid: Optional[int] = None
    status: str = "stopped"  # stopped, starting, running, failed
    restart_count: int = 0
    last_error: Optional[str] = None
    is_ready: bool = False  # True when MCP server is ready


class AgentSupervisor:
    """Supervises agent processes - starting, monitoring, and stopping them.
    
    Each agent runs in its own process for:
    - Isolation (one crash doesn't affect others)
    - True parallelism (no GIL)
    - Clean shutdown
    - Resource management
    """
    
    def __init__(self, log_dir: str = "logs"):
        self.agents: Dict[str, AgentProcess] = {}
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Supervisor's own logger
        self.logger = AgentLogger(
            agent_id="supervisor",
            log_level="INFO",
            log_file=str(self.log_dir / "supervisor.log")
        )
        
        self._monitor_task: Optional[asyncio.Task] = None
        self._shutdown_event = asyncio.Event()
        
        # Initialize connection manager
        self.connection_manager = ConnectionManager()
    
    def add_agent(self, config: AgentConfig):
        """Add an agent to be supervised."""
        if config.name in self.agents:
            self.logger.warning(f"Agent {config.name} already exists")
            return
        
        self.agents[config.name] = AgentProcess(config=config)
        self.logger.info(f"Added agent {config.name} to supervisor")
    
    async def start_agent(self, agent_name: str, monitor_output: bool = True) -> bool:
        """Start a single agent process."""
        if agent_name not in self.agents:
            self.logger.error(f"Agent {agent_name} not found")
            return False
        
        agent_proc = self.agents[agent_name]
        
        if agent_proc.status == "running":
            self.logger.warning(f"Agent {agent_name} already running")
            return True
        
        agent_proc.status = "starting"
        
        try:
            # Prepare agent runner command
            cmd = [
                sys.executable,
                "-m", "agent_framework.network.agent_runner",
                "--config", json.dumps(agent_proc.config.__dict__),
                "--available-agents", ",".join(self.agents.keys())
            ]
            
            # Set up process environment
            env = subprocess.os.environ.copy()
            
            # Start process
            agent_proc.process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,  # Enable stdin for commands
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env,
                # Important: start new process group for clean shutdown
                preexec_fn=subprocess.os.setsid if sys.platform != "win32" else None,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == "win32" else 0
            )
            
            agent_proc.pid = agent_proc.process.pid
            agent_proc.status = "running"
            
            self.logger.info(
                f"Started agent {agent_name} (PID: {agent_proc.pid})"
            )
            
            # Register agent with connection manager
            self.connection_manager.register_agent(agent_name, agent_proc.config.port)
            
            # Start monitoring stdout/stderr in background 
            if monitor_output:
                asyncio.create_task(self._monitor_agent_output(agent_name))
            else:
                # Even without monitoring, we need to consume output to prevent buffer blocking
                asyncio.create_task(self._consume_agent_output(agent_name))
            
            return True
            
        except Exception as e:
            agent_proc.status = "failed"
            agent_proc.last_error = str(e)
            self.logger.error(f"Failed to start agent {agent_name}: {e}")
            return False
    
    async def _monitor_agent_output(self, agent_name: str):
        """Monitor agent process output and log it."""
        agent_proc = self.agents[agent_name]
        if not agent_proc.process:
            return
        
        # Read stdout
        async def read_stream(stream, prefix):
            while True:
                line = stream.readline()
                if not line:
                    break
                
                # Log agent output with prefix
                decoded = line.decode('utf-8', errors='replace').strip()
                if decoded:
                    self.logger.info(f"[{agent_name}] {decoded}")
                    
                    # Check for READY signal
                    if decoded == "READY":
                        agent_proc = self.agents.get(agent_name)
                        if agent_proc:
                            agent_proc.is_ready = True
        
        # Monitor both stdout and stderr
        if agent_proc.process.stdout:
            asyncio.create_task(
                asyncio.to_thread(
                    lambda: asyncio.run(read_stream(agent_proc.process.stdout, "OUT"))
                )
            )
        
        if agent_proc.process.stderr:
            asyncio.create_task(
                asyncio.to_thread(
                    lambda: asyncio.run(read_stream(agent_proc.process.stderr, "ERR"))
                )
            )
    
    async def _consume_agent_output(self, agent_name: str):
        """Consume agent output without logging to prevent buffer blocking."""
        agent_proc = self.agents[agent_name]
        if not agent_proc.process:
            return
        
        # Just consume output in a thread to prevent blocking
        def consume_blocking():
            for line in agent_proc.process.stdout:
                decoded = line.decode('utf-8', errors='replace').strip()
                if decoded == "READY":
                    agent_proc.is_ready = True
        
        if agent_proc.process.stdout:
            asyncio.create_task(
                asyncio.to_thread(consume_blocking)
            )
    
    async def stop_agent(self, agent_name: str, timeout: float = 10.0):
        """Stop a single agent gracefully."""
        if agent_name not in self.agents:
            return
        
        agent_proc = self.agents[agent_name]
        if agent_proc.status != "running" or not agent_proc.process:
            return
        
        self.logger.info(f"Stopping agent {agent_name}")
        
        try:
            # First try to send SHUTDOWN command via stdin
            if agent_proc.process.stdin:
                try:
                    agent_proc.process.stdin.write(b"SHUTDOWN\n")
                    agent_proc.process.stdin.flush()
                    # Give it a moment to shut down gracefully
                    await asyncio.sleep(0.5)
                except:
                    pass
            
            # Then send SIGTERM for graceful shutdown
            if sys.platform == "win32":
                agent_proc.process.terminate()
            else:
                subprocess.os.kill(agent_proc.pid, signal.SIGTERM)
            
            # Wait for process to exit
            try:
                agent_proc.process.wait(timeout=timeout)
            except subprocess.TimeoutExpired:
                # Force kill if not responding
                self.logger.warning(f"Agent {agent_name} not responding, force killing")
                
                if sys.platform == "win32":
                    agent_proc.process.kill()
                else:
                    subprocess.os.kill(agent_proc.pid, signal.SIGKILL)
                
                agent_proc.process.wait()
            
            agent_proc.status = "stopped"
            agent_proc.process = None
            agent_proc.pid = None
            agent_proc.is_ready = False
            
            self.logger.info(f"Agent {agent_name} stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping agent {agent_name}: {e}")
    
    async def start_all(self, monitor: bool = True):
        """Start all registered agents with two-phase startup.
        
        Args:
            monitor: If True, start background monitoring. If False, just start agents.
        """
        self.logger.info("Starting all agents")
        
        # Phase 1: Start all agents and their MCP servers
        for agent_name in self.agents:
            await self.start_agent(agent_name, monitor_output=monitor)
            await asyncio.sleep(0.5)  # Give each agent time to bind to port
        
        # Wait for all agents to report READY
        self.logger.info("Waiting for all agents to be ready...")
        await self._wait_for_all_ready()
        
        # Phase 2: Tell all agents to connect to peers
        self.logger.info("All agents ready, initiating peer connections...")
        await self._connect_all_agents()
        
        # Start monitoring only if requested
        if monitor and not self._monitor_task:
            self._monitor_task = asyncio.create_task(self._monitor_loop())
    
    async def stop_all(self):
        """Stop all running agents gracefully."""
        self.logger.info("Stopping all agents")
        
        # Signal monitor to stop
        self._shutdown_event.set()
        
        # Stop all agents in parallel
        tasks = [
            self.stop_agent(name) 
            for name in self.agents
        ]
        await asyncio.gather(*tasks, return_exceptions=True)
        
        # Cancel monitor task
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
    
    async def _monitor_loop(self):
        """Monitor agent processes and restart failed ones."""
        while not self._shutdown_event.is_set():
            try:
                for agent_name, agent_proc in self.agents.items():
                    if agent_proc.status != "running" or not agent_proc.process:
                        continue
                    
                    # Check if process is still alive
                    poll_result = agent_proc.process.poll()
                    
                    if poll_result is not None:
                        # Process has exited
                        agent_proc.status = "failed"
                        agent_proc.process = None
                        agent_proc.pid = None
                        
                        self.logger.error(
                            f"Agent {agent_name} crashed (exit code: {poll_result})"
                        )
                        
                        # Auto-restart if under restart limit
                        if agent_proc.restart_count < 3:
                            agent_proc.restart_count += 1
                            self.logger.info(
                                f"Restarting agent {agent_name} "
                                f"(attempt {agent_proc.restart_count}/3)"
                            )
                            await self.start_agent(agent_name)
                        else:
                            self.logger.error(
                                f"Agent {agent_name} failed too many times, "
                                "not restarting"
                            )
                
                # Check every 5 seconds
                await asyncio.sleep(5)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Monitor loop error: {e}")
                await asyncio.sleep(5)
    
    def get_status(self) -> Dict[str, Dict[str, any]]:
        """Get status of all agents."""
        status = {}
        
        for name, agent_proc in self.agents.items():
            status[name] = {
                "status": agent_proc.status,
                "pid": agent_proc.pid,
                "port": agent_proc.config.port,
                "restart_count": agent_proc.restart_count,
                "last_error": agent_proc.last_error,
                "is_ready": agent_proc.is_ready
            }
            
            # Add resource usage if running
            if agent_proc.pid and agent_proc.status == "running":
                try:
                    process = psutil.Process(agent_proc.pid)
                    status[name].update({
                        "cpu_percent": process.cpu_percent(),
                        "memory_mb": process.memory_info().rss / 1024 / 1024
                    })
                except:
                    pass
        
        return status
    
    async def restart_agent(self, agent_name: str):
        """Restart a specific agent."""
        self.logger.info(f"Restarting agent {agent_name}")
        
        await self.stop_agent(agent_name)
        await asyncio.sleep(1)  # Brief pause
        
        # Reset restart count on manual restart
        self.agents[agent_name].restart_count = 0
        
        await self.start_agent(agent_name)
    
    async def _wait_for_all_ready(self, timeout: int = 30):
        """Wait for all agents to report they are ready."""
        start_time = asyncio.get_event_loop().time()
        
        while True:
            all_ready = all(
                agent.is_ready for agent in self.agents.values()
                if agent.status == "running"
            )
            
            if all_ready:
                self.logger.info("All agents are ready")
                return
            
            if asyncio.get_event_loop().time() - start_time > timeout:
                not_ready = [
                    name for name, agent in self.agents.items()
                    if agent.status == "running" and not agent.is_ready
                ]
                raise TimeoutError(f"Agents not ready after {timeout}s: {not_ready}")
            
            await asyncio.sleep(0.5)
    
    async def _connect_all_agents(self):
        """Send CONNECT command to all agents to initiate peer connections."""
        for name, agent_proc in self.agents.items():
            if agent_proc.status == "running" and agent_proc.process:
                try:
                    # Send CONNECT command to agent's stdin
                    agent_proc.process.stdin.write(b"CONNECT\n")
                    agent_proc.process.stdin.flush()
                    self.logger.info(f"Sent CONNECT signal to {name}")
                except Exception as e:
                    self.logger.error(f"Failed to send CONNECT to {name}: {e}")
    
    async def connect(self, from_agent: str, to_agent: str, bidirectional: bool = False):
        """Connect one agent to another.
        
        Args:
            from_agent: Name of the agent that will connect
            to_agent: Name of the agent to connect to
            bidirectional: If True, also create reverse connection
        """
        # Ensure both agents are running
        if from_agent not in self.agents or self.agents[from_agent].status != "running":
            raise ValueError(f"Agent {from_agent} is not running")
        if to_agent not in self.agents or self.agents[to_agent].status != "running":
            raise ValueError(f"Agent {to_agent} is not running")
        
        # Connect from_agent -> to_agent
        success = await self.connection_manager.connect_agents(
            from_agent, to_agent, self.agents
        )
        
        if not success:
            raise RuntimeError(f"Failed to connect {from_agent} to {to_agent}")
        
        # If bidirectional, also connect to_agent -> from_agent
        if bidirectional:
            success = await self.connection_manager.connect_agents(
                to_agent, from_agent, self.agents
            )
            if not success:
                raise RuntimeError(f"Failed to connect {to_agent} to {from_agent}")
        
        self.logger.info(
            f"Connected {from_agent} {'<->' if bidirectional else '->'} {to_agent}"
        )
