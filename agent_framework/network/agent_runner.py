"""Simple agent runner that runs everything in one process.

This uses FastMCP's run_async() to avoid event loop conflicts.
"""

import asyncio
import sys
import os
import json
import argparse
import signal
import threading

from agent_framework.core.config import AgentConfig, load_config
from agent_framework.core.agent import Agent
from agent_framework.network.control_socket import AgentControlSocket


class SimpleAgentRunner:
    """Runs an agent in a single process."""
    
    def __init__(self, config: AgentConfig, available_agents: list[str]):
        self.config = config
        self.available_agents = available_agents
        self.agent = None
        self._shutdown_event = asyncio.Event()
    
    async def run(self):
        """Run the agent."""
        # Setup signal handlers
        loop = asyncio.get_event_loop()
        for sig in (signal.SIGTERM, signal.SIGINT):
            loop.add_signal_handler(sig, lambda: asyncio.create_task(self._handle_shutdown()))
        
        try:
            # Create and start agent
            self.agent = Agent(self.config, self.available_agents)
            self.agent._shutdown_event = self._shutdown_event  # Share shutdown event
            
            # Start the agent (includes MCP server)
            server_task = asyncio.create_task(self.agent.start())
            
            # Wait a moment for server to start
            await asyncio.sleep(2)
            
            print(f"Agent {self.config.name} running on port {self.config.port}", flush=True)
            
            if hasattr(self, 'use_socket') and self.use_socket:
                # Socket mode - no CPU spin
                socket_path = f"/tmp/chaotic-af/agent-{self.config.name}.sock"
                # Pass the runner's shutdown event to control socket
                control = AgentControlSocket(self.agent, socket_path, self._shutdown_event)
                socket_server = await control.start()
                
                print("READY", flush=True)  # Signal to supervisor
                
                # Create server task
                server_task = asyncio.create_task(socket_server.serve_forever())
                
                # Wait for shutdown event
                await self._shutdown_event.wait()
                
                # Stop socket server
                socket_server.close()
                await socket_server.wait_closed()
                
                # Cancel server task
                server_task.cancel()
                try:
                    await server_task
                except asyncio.CancelledError:
                    pass
                
                print(f"Agent {self.config.name} shutting down gracefully", flush=True)
                return
            
            print("READY", flush=True)  # Signal to supervisor
            
            # Wait for CONNECT command
            connect_task = asyncio.create_task(self.wait_for_connect_command())
            shutdown_task = asyncio.create_task(self._shutdown_event.wait())
            
            done, pending = await asyncio.wait(
                [connect_task, shutdown_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            
            for task in pending:
                task.cancel()
            
            if connect_task in done and connect_task.result():
                await self.agent.connect_to_peers()
                print(f"Agent {self.config.name} connected to peers", flush=True)
                
                # Continue listening for dynamic connections and shutdown
                asyncio.create_task(self._listen_for_commands())
                
                # Wait for shutdown
                await self._shutdown_event.wait()
                print(f"Agent {self.config.name} shutting down gracefully", flush=True)
            
        except Exception as e:
            print(f"Agent {self.config.name} failed: {str(e)}", file=sys.stderr, flush=True)
            import traceback
            traceback.print_exc()
            sys.exit(1)
        finally:
            if self.agent:
                await self.agent.stop()
            print(f"Agent {self.config.name} stopped", flush=True)
    
    async def wait_for_connect_command(self):
        """Wait for CONNECT command on stdin."""
        while not self._shutdown_event.is_set():
            line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
            line = line.strip()
            
            if line == "CONNECT":
                print(f"Agent {self.config.name} received connect signal", flush=True)
                return True
            elif line.startswith("CONNECT:"):
                # Dynamic connection command: CONNECT:agent_name:endpoint
                parts = line.split(":", 2)  # Split only on first 2 colons
                if len(parts) == 3:
                    _, target_agent, endpoint = parts
                    print(f"Agent {self.config.name} received CONNECT:{target_agent}:{endpoint}", flush=True)
                    
                    # Add connection dynamically
                    success = await self.agent.mcp_client.add_connection(target_agent, endpoint)
                    if success:
                        print(f"Agent {self.config.name} connected to {target_agent}", flush=True)
                        
                        # Update the server's available connections if using universal server
                        if hasattr(self.agent, 'mcp_server') and hasattr(self.agent.mcp_server, 'update_connections'):
                            current_connections = list(self.agent.mcp_client.connections.keys())
                            self.agent.mcp_server.update_connections(current_connections)
                            print(f"Agent {self.config.name} updated available connections: {current_connections}", flush=True)
                    else:
                        print(f"Agent {self.config.name} failed to connect to {target_agent}", flush=True)
                continue
            elif line == "SHUTDOWN":
                print(f"Agent {self.config.name} received SHUTDOWN command", flush=True)
                self._shutdown_event.set()
                return False
    
    async def _listen_for_commands(self):
        """Continue listening for dynamic commands after initial connect."""
        while not self._shutdown_event.is_set():
            try:
                line = await asyncio.get_event_loop().run_in_executor(None, sys.stdin.readline)
                line = line.strip()
                
                if line.startswith("CONNECT:"):
                    # Dynamic connection command: CONNECT:agent_name:endpoint
                    parts = line.split(":", 2)
                    if len(parts) == 3:
                        _, target_agent, endpoint = parts
                        print(f"Agent {self.config.name} received CONNECT:{target_agent}:{endpoint}", flush=True)
                        
                        # Add connection dynamically
                        success = await self.agent.mcp_client.add_connection(target_agent, endpoint)
                        if success:
                            print(f"Agent {self.config.name} connected to {target_agent}", flush=True)
                            
                            # Update the server's available connections
                            if hasattr(self.agent, 'mcp_server') and hasattr(self.agent.mcp_server, 'update_connections'):
                                current_connections = list(self.agent.mcp_client.connections.keys())
                                self.agent.mcp_server.update_connections(current_connections)
                                print(f"Agent {self.config.name} updated available connections: {current_connections}", flush=True)
                        else:
                            print(f"Agent {self.config.name} failed to connect to {target_agent}", flush=True)
                elif line == "SHUTDOWN":
                    self._shutdown_event.set()
                    break
            except Exception as e:
                if not self._shutdown_event.is_set():
                    print(f"Error in command listener: {e}", file=sys.stderr, flush=True)
                break
    
    async def _handle_shutdown(self):
        """Handle shutdown signals."""
        print(f"Agent {self.config.name} received shutdown signal", flush=True)
        self._shutdown_event.set()


def main():
    """Entry point."""
    parser = argparse.ArgumentParser(description="Run an agent")
    parser.add_argument("--config", required=True, help="JSON-encoded agent configuration")
    parser.add_argument("--available-agents", required=True, help="Comma-separated list of agent names")
    parser.add_argument("--use-socket", action="store_true", default=True, help="Use socket for control (default: True)")
    parser.add_argument("--use-stdin", action="store_true", help="Use legacy stdin for control")
    
    args = parser.parse_args()
    
    # Parse config
    config_dict = json.loads(args.config)
    config = AgentConfig(**config_dict)
    available_agents = args.available_agents.split(',')
    
    # Run agent
    runner = SimpleAgentRunner(config, available_agents)
    # Use stdin if explicitly requested, otherwise use socket
    runner.use_socket = not args.use_stdin
    
    # Set up signal handlers
    def signal_handler(signum, frame):
        print(f"Agent {config.name} received signal {signum}", flush=True)
        runner._shutdown_event.set()
    
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # Run the agent
    asyncio.run(runner.run())


if __name__ == "__main__":
    main()
