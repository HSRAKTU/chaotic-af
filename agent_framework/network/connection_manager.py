"""Dynamic connection management for agents.

This module provides runtime connection management between agents,
replacing the hardcoded port mapping.
"""

from typing import Dict, Tuple, Optional
import asyncio
import sys
import os
import json
from dataclasses import dataclass
from ..core.logging import setup_logging

import logging
logger = logging.getLogger(__name__)


@dataclass
class ConnectionRequest:
    """Request to connect one agent to another."""
    from_agent: str
    to_agent: str
    to_port: int
    bidirectional: bool = False


class ConnectionManager:
    """Manages dynamic connections between agents."""
    
    def __init__(self):
        self.agent_registry: Dict[str, int] = {}  # agent_name -> port
        self.connections: Dict[Tuple[str, str], bool] = {}  # (from, to) -> connected
        
    def register_agent(self, name: str, port: int):
        """Register an agent with its port."""
        self.agent_registry[name] = port
        logger.info(f"Registered agent {name} on port {port}")
        print(f"ConnectionManager: Registered {name} at {self.get_agent_endpoint(name)}", flush=True)
    
    def get_agent_endpoint(self, name: str) -> Optional[str]:
        """Get the endpoint URL for an agent."""
        if name not in self.agent_registry:
            return None
        port = self.agent_registry[name]
        return f"http://localhost:{port}/mcp"
    
    async def connect_agents(self, from_agent: str, to_agent: str, agent_processes: Dict) -> bool:
        """Connect one agent to another.
        
        This sends a command to the from_agent's process to add a connection.
        """
        if from_agent not in agent_processes or to_agent not in self.agent_registry:
            logger.error(f"Unknown agents: {from_agent} or {to_agent}")
            print(f"ConnectionManager: Source agent {from_agent} not found or not running.", file=sys.stderr, flush=True)
            return False
        
        # Get the target endpoint
        to_endpoint = self.get_agent_endpoint(to_agent)
        if not to_endpoint:
            logger.error(f"No endpoint found for {to_agent}")
            print(f"ConnectionManager: Target agent {to_agent} not registered.", file=sys.stderr, flush=True)
            return False
        
        # Try socket first, then fall back to stdin
        agent_proc = agent_processes[from_agent]
        
        # Try socket first
        socket_path = f"/tmp/chaotic-af/agent-{from_agent}.sock"
        if os.path.exists(socket_path):
            try:
                reader, writer = await asyncio.open_unix_connection(socket_path)
                cmd = {
                    'cmd': 'connect',
                    'target': to_agent,
                    'endpoint': to_endpoint
                }
                writer.write(json.dumps(cmd).encode() + b'\n')
                await writer.drain()
                
                response = await reader.readline()
                writer.close()
                await writer.wait_closed()
                
                result = json.loads(response.decode())
                if result.get('status') == 'connected':
                    self.connections[(from_agent, to_agent)] = True
                    print(f"ConnectionManager: Connected {from_agent} -> {to_agent} via socket", file=sys.stderr, flush=True)
                    return True
            except Exception as e:
                print(f"ConnectionManager: Socket failed, falling back to stdin: {e}", file=sys.stderr, flush=True)
        
        # Fall back to stdin
        if agent_proc.process and agent_proc.process.stdin:
            command = f"CONNECT:{to_agent}:{to_endpoint}\n"
            try:
                agent_proc.process.stdin.write(command.encode())
                agent_proc.process.stdin.flush()
                
                # Mark connection as established
                self.connections[(from_agent, to_agent)] = True
                logger.info(f"Connected {from_agent} -> {to_agent}")
                print(f"ConnectionManager: Sent connect command from {from_agent} to {to_agent} ({to_endpoint})", flush=True)
                return True
                
            except Exception as e:
                logger.error(f"Failed to send connect command: {e}")
                print(f"ConnectionManager: Failed to send connect command to {from_agent}: {e}", file=sys.stderr, flush=True)
                return False
        else:
            print(f"ConnectionManager: Agent {from_agent} process or stdin not available", file=sys.stderr, flush=True)
        
        return False
    
    def get_connections(self) -> Dict[Tuple[str, str], bool]:
        """Get all established connections."""
        return self.connections.copy()
    
    def is_connected(self, from_agent: str, to_agent: str) -> bool:
        """Check if two agents are connected."""
        return self.connections.get((from_agent, to_agent), False)
