"""Agent Framework - Build multi-agent systems with ease.

A Python framework for creating collaborative AI agent networks using
the Model Context Protocol (MCP).
"""

__version__ = "0.1.0"

# Core components
from .core.agent import Agent
from .core.config import AgentConfig, load_config
from .core.events import EventStream, EventType, AgentEvent
from .core.logging import AgentLogger

# Network components
from .network.supervisor import AgentSupervisor
from .network.registry import AgentRegistry

# MCP components
from .mcp.server_universal import UniversalAgentMCPServer
from .mcp.client import AgentMCPClient

__all__ = [
    # Core
    "Agent",
    "AgentConfig",
    "load_config",
    "EventStream",
    "EventType", 
    "AgentEvent",
    "AgentLogger",
    
    # Network
    "AgentSupervisor",
    "AgentRegistry",
    
    # MCP
    "UniversalAgentMCPServer",
    "AgentMCPClient",
]
