"""Agent registry for service discovery.

Requirements:
- Track available agents and their endpoints
- Support dynamic registration/deregistration
- Provide agent discovery
"""

from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timezone
import asyncio


@dataclass
class AgentInfo:
    """Information about a registered agent."""
    name: str
    url: str
    port: int
    role: str
    status: str = "active"
    last_seen: datetime = None
    
    def __post_init__(self):
        if not self.last_seen:
            self.last_seen = datetime.now(timezone.utc)


class AgentRegistry:
    """Registry for agent discovery and management.
    
    In a production system, this would be backed by a distributed
    service like etcd, consul, or redis. For now, it's in-memory.
    """
    
    def __init__(self):
        self._agents: Dict[str, AgentInfo] = {}
        self._lock = asyncio.Lock()
    
    async def register(self, name: str, url: str, port: int, role: str):
        """Register an agent."""
        async with self._lock:
            self._agents[name] = AgentInfo(
                name=name,
                url=url,
                port=port,
                role=role
            )
    
    async def deregister(self, name: str):
        """Remove an agent from registry."""
        async with self._lock:
            self._agents.pop(name, None)
    
    async def get_agent(self, name: str) -> Optional[AgentInfo]:
        """Get info for a specific agent."""
        async with self._lock:
            return self._agents.get(name)
    
    async def get_all_agents(self) -> List[AgentInfo]:
        """Get all registered agents."""
        async with self._lock:
            return list(self._agents.values())
    
    async def update_status(self, name: str, status: str):
        """Update agent status."""
        async with self._lock:
            if name in self._agents:
                self._agents[name].status = status
                self._agents[name].last_seen = datetime.now(timezone.utc)
    
    def get_agent_url(self, name: str) -> Optional[str]:
        """Get URL for an agent (sync method for compatibility)."""
        return self._agents.get(name, {}).get('url')
    
    def get_active_agents(self) -> List[str]:
        """Get names of all active agents."""
        return [
            name for name, info in self._agents.items()
            if info.status == "active"
        ]
