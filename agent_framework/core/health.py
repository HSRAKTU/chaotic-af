"""Health monitoring and auto-recovery for agents."""

import asyncio
import time
import json
from typing import Dict, Optional, Callable
from dataclasses import dataclass, field
from datetime import datetime

from ..core.logging import AgentLogger


@dataclass
class HealthStatus:
    """Health status of an agent."""
    name: str
    healthy: bool
    last_check: float
    consecutive_failures: int = 0
    last_error: Optional[str] = None
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "healthy": self.healthy, 
            "last_check": self.last_check,
            "last_check_iso": datetime.fromtimestamp(self.last_check).isoformat(),
            "consecutive_failures": self.consecutive_failures,
            "last_error": self.last_error
        }


@dataclass
class HealthConfig:
    """Configuration for health monitoring."""
    check_interval: float = 5.0  # seconds between checks
    failure_threshold: int = 3   # consecutive failures before restart
    restart_delay: float = 2.0   # delay before restart
    max_restarts: int = 5        # max restarts per hour
    socket_timeout: float = 2.0  # timeout for socket operations


class HealthMonitor:
    """Monitors agent health and handles recovery."""
    
    def __init__(self, supervisor, config: Optional[HealthConfig] = None):
        self.supervisor = supervisor
        self.config = config or HealthConfig()
        self.logger = AgentLogger("health_monitor", "INFO")
        self._running = False
        self._monitor_task = None
        self._health_status: Dict[str, HealthStatus] = {}
        self._restart_counts: Dict[str, list] = {}  # Track restart timestamps
        
    async def start(self):
        """Start health monitoring."""
        if self._running:
            return
            
        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        self.logger.info("Health monitoring started")
        
    async def stop(self):
        """Stop health monitoring."""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        self.logger.info("Health monitoring stopped")
        
    async def _monitor_loop(self):
        """Main monitoring loop."""
        while self._running:
            try:
                await self._check_all_agents()
                await asyncio.sleep(self.config.check_interval)
            except Exception as e:
                self.logger.error(f"Error in monitor loop: {e}")
                await asyncio.sleep(self.config.check_interval)
                
    async def _check_all_agents(self):
        """Check health of all agents."""
        for agent_name, agent_proc in self.supervisor.agents.items():
            if agent_proc.status != "running":
                continue
                
            # Initialize health status if needed
            if agent_name not in self._health_status:
                self._health_status[agent_name] = HealthStatus(
                    name=agent_name,
                    healthy=True,
                    last_check=time.time()
                )
                
            await self._check_agent_health(agent_name, agent_proc)
            
    async def _check_agent_health(self, agent_name: str, agent_proc):
        """Check health of a single agent."""
        health_status = self._health_status[agent_name]
        
        try:
            # First check if process is alive
            if agent_proc.process and agent_proc.process.poll() is not None:
                # Process died
                self._handle_health_failure(
                    health_status, 
                    f"Process died (exit code: {agent_proc.process.returncode})"
                )
                await self._handle_recovery(agent_name, agent_proc)
                return
                
            # Check via socket if in socket mode
            if self.supervisor.use_sockets:
                socket_path = f"/tmp/chaotic-af/agent-{agent_name}.sock"
                healthy = await self._check_socket_health(socket_path)
                
                if healthy:
                    self._handle_health_success(health_status)
                else:
                    self._handle_health_failure(health_status, "Socket health check failed")
                    
                    # Check if we should restart
                    if health_status.consecutive_failures >= self.config.failure_threshold:
                        await self._handle_recovery(agent_name, agent_proc)
                        
        except Exception as e:
            self.logger.error(f"Error checking health of {agent_name}: {e}")
            self._handle_health_failure(health_status, str(e))
            
    async def _check_socket_health(self, socket_path: str) -> bool:
        """Check agent health via socket."""
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_unix_connection(socket_path),
                timeout=self.config.socket_timeout
            )
            
            # Send health command
            cmd = {"cmd": "health"}
            writer.write(json.dumps(cmd).encode() + b'\n')
            await writer.drain()
            
            # Read response
            response = await asyncio.wait_for(
                reader.readline(),
                timeout=self.config.socket_timeout
            )
            
            writer.close()
            await writer.wait_closed()
            
            if response:
                result = json.loads(response.decode())
                return result.get("status") == "ready"
                
            return False
            
        except (asyncio.TimeoutError, ConnectionRefusedError, FileNotFoundError):
            return False
        except Exception as e:
            self.logger.debug(f"Socket health check error: {e}")
            return False
            
    def _handle_health_success(self, health_status: HealthStatus):
        """Handle successful health check."""
        health_status.healthy = True
        health_status.last_check = time.time()
        health_status.consecutive_failures = 0
        health_status.last_error = None
        
    def _handle_health_failure(self, health_status: HealthStatus, error: str):
        """Handle failed health check."""
        health_status.healthy = False
        health_status.last_check = time.time()
        health_status.consecutive_failures += 1
        health_status.last_error = error
        
        self.logger.warning(
            f"Health check failed for {health_status.name}: {error} "
            f"(failures: {health_status.consecutive_failures})"
        )
        
    async def _handle_recovery(self, agent_name: str, agent_proc):
        """Handle agent recovery/restart."""
        # Check restart limit
        if not self._can_restart(agent_name):
            self.logger.error(
                f"Agent {agent_name} exceeded restart limit, not restarting"
            )
            # Mark agent as stopped in supervisor
            if agent_name in self.supervisor.agents:
                self.supervisor.agents[agent_name].status = "stopped"
            return
            
        self.logger.info(f"Attempting to restart agent {agent_name}")
        
        try:
            # Stop the agent first
            await self.supervisor.stop_agent(agent_name, timeout=5.0)
            
            # Wait before restart
            await asyncio.sleep(self.config.restart_delay)
            
            # Restart the agent
            success = await self.supervisor.start_agent(agent_name, monitor_output=False)
            
            if success:
                # Wait for agent to be ready
                await asyncio.sleep(2)
                
                # Track restart
                self._track_restart(agent_name)
                
                # Wait for socket to be available
                socket_ready = False
                for _ in range(5):  # Try for 5 seconds
                    if await self._check_socket_health(agent_name):
                        socket_ready = True
                        break
                    await asyncio.sleep(1)
                
                # Reset health status based on socket readiness
                self._health_status[agent_name] = HealthStatus(
                    name=agent_name,
                    healthy=socket_ready,
                    last_check=time.time()
                )
                
                self.logger.info(f"Successfully restarted agent {agent_name}")
            else:
                self.logger.error(f"Failed to restart agent {agent_name}")
                
        except Exception as e:
            self.logger.error(f"Error restarting agent {agent_name}: {e}")
            
    def _can_restart(self, agent_name: str) -> bool:
        """Check if agent can be restarted based on restart limit."""
        now = time.time()
        hour_ago = now - 3600
        
        # Get restart timestamps for this agent
        if agent_name not in self._restart_counts:
            self._restart_counts[agent_name] = []
            
        # Remove old timestamps
        self._restart_counts[agent_name] = [
            ts for ts in self._restart_counts[agent_name] 
            if ts > hour_ago
        ]
        
        # Check limit
        return len(self._restart_counts[agent_name]) < self.config.max_restarts
        
    def _track_restart(self, agent_name: str):
        """Track agent restart."""
        if agent_name not in self._restart_counts:
            self._restart_counts[agent_name] = []
        self._restart_counts[agent_name].append(time.time())
        
    def get_health_status(self) -> Dict[str, Dict]:
        """Get current health status of all agents."""
        return {
            name: status.to_dict() 
            for name, status in self._health_status.items()
        }
