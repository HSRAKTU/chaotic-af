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
from ..client.socket_client import AgentSocketClient

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
        
        # Use AgentSocketClient for connection
        result = await AgentSocketClient.connect_agents(
            from_agent, to_agent, to_endpoint
        )
        
        if result.get('status') == 'connected':
            self.connections[(from_agent, to_agent)] = True
            print(f"ConnectionManager: Connected {from_agent} -> {to_agent} via socket", file=sys.stderr, flush=True)
            return True
        else:
            error = result.get('error', 'Unknown error')
            print(f"ConnectionManager: Socket connection failed: {error}", file=sys.stderr, flush=True)
            logger.error(f"Failed to send connect command via socket: {error}")
            return False
    
    def get_connections(self) -> Dict[Tuple[str, str], bool]:
        """Get all established connections."""
        return self.connections.copy()
    
    def is_connected(self, from_agent: str, to_agent: str) -> bool:
        """Check if two agents are connected."""
        return self.connections.get((from_agent, to_agent), False)
