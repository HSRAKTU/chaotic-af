"""Structured logging system for agent framework.

Requirements:
- Agent-prefixed logs for clear identification
- Structured format for tool calls and responses
- File and console output
- Different log levels
- Correlation IDs for tracking related events
"""

import logging
import json
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import sys
from pathlib import Path


class AgentLogFormatter(logging.Formatter):
    """Custom formatter for agent logs with structured output."""
    
    # ANSI color codes for different agents
    AGENT_COLORS = {
        'alice': '\033[95m',      # Magenta
        'bob': '\033[94m',        # Blue
        'charlie': '\033[93m',    # Yellow
        'coordinator': '\033[92m', # Green
        'researcher': '\033[96m',  # Cyan
        'writer': '\033[91m',      # Red
        'supervisor': '\033[90m',  # Gray
    }
    RESET_COLOR = '\033[0m'
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        # Get color for this agent, or generate one from hash
        if agent_id.lower() in self.AGENT_COLORS:
            self.color = self.AGENT_COLORS[agent_id.lower()]
        else:
            # Generate a color from the agent ID hash
            colors = ['\033[91m', '\033[92m', '\033[93m', '\033[94m', '\033[95m', '\033[96m']
            self.color = colors[hash(agent_id) % len(colors)]
        super().__init__()
    
    def format(self, record):
        # Base format: [timestamp] [AGENT_ID] [LEVEL] message
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
        # Add color to agent ID
        colored_agent = f"{self.color}{self.agent_id}{self.RESET_COLOR}"
        base_msg = f"[{timestamp}] [{colored_agent}] [{record.levelname}] {record.getMessage()}"
        
        # Add structured data if present
        if hasattr(record, 'event_type'):
            base_msg += f"\n  Event: {record.event_type}"
        
        if hasattr(record, 'tool_name'):
            base_msg += f"\n  Tool: {record.tool_name}"
        
        if hasattr(record, 'payload'):
            # Pretty print payload
            payload_str = json.dumps(record.payload, indent=2)
            base_msg += f"\n  Payload: {payload_str}"
        
        if hasattr(record, 'response'):
            # Truncate long responses
            response_str = str(record.response)
            if len(response_str) > 500:
                response_str = response_str[:500] + "... (truncated)"
            base_msg += f"\n  Response: {response_str}"
        
        if hasattr(record, 'correlation_id'):
            base_msg += f"\n  Correlation ID: {record.correlation_id}"
        
        if hasattr(record, 'error'):
            base_msg += f"\n  Error: {record.error}"
        
        return base_msg


class AgentLogger:
    """Logger for an individual agent with structured logging support."""
    
    def __init__(self, agent_id: str, log_level: str = "INFO", 
                 log_file: Optional[str] = None):
        self.agent_id = agent_id
        self.logger = logging.getLogger(f"agent.{agent_id}")
        self.logger.setLevel(getattr(logging, log_level))
        
        # Remove existing handlers to avoid duplicates
        self.logger.handlers.clear()
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(AgentLogFormatter(agent_id))
        self.logger.addHandler(console_handler)
        
        # File handler if specified
        if log_file:
            # Ensure log directory exists
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(AgentLogFormatter(agent_id))
            self.logger.addHandler(file_handler)
    
    def log_tool_call_received(self, tool_name: str, from_agent: str, 
                              payload: Dict[str, Any], correlation_id: Optional[str] = None):
        """Log incoming tool call from another agent."""
        self.logger.info(
            f"Tool call received: {tool_name}",
            extra={
                "event_type": "TOOL_CALL_RECEIVED",
                "tool_name": tool_name,
                "from_agent": from_agent,
                "payload": payload,
                "correlation_id": correlation_id
            }
        )
    
    def log_tool_call_making(self, tool_name: str, to_target: str,
                            payload: Dict[str, Any], correlation_id: Optional[str] = None):
        """Log outgoing tool call to another agent or MCP server."""
        self.logger.info(
            f"Making tool call: {tool_name}",
            extra={
                "event_type": "TOOL_CALL_MAKING",
                "tool_name": tool_name,
                "to_target": to_target,
                "payload": payload,
                "correlation_id": correlation_id
            }
        )
    
    def log_tool_response(self, tool_name: str, response: Any, 
                         success: bool = True, correlation_id: Optional[str] = None):
        """Log tool call response."""
        level = logging.INFO if success else logging.ERROR
        self.logger.log(
            level,
            f"Tool response: {tool_name} - {'Success' if success else 'Failed'}",
            extra={
                "event_type": "TOOL_CALL_RESPONSE",
                "tool_name": tool_name,
                "response": response,
                "success": success,
                "correlation_id": correlation_id
            }
        )
    
    def log_llm_reasoning(self, reasoning: str, correlation_id: Optional[str] = None):
        """Log LLM reasoning process."""
        self.logger.debug(
            "LLM reasoning",
            extra={
                "event_type": "LLM_REASONING",
                "reasoning": reasoning,
                "correlation_id": correlation_id
            }
        )
    
    def log_agent_communication(self, direction: str, other_agent: str,
                               message: str, correlation_id: Optional[str] = None):
        """Log inter-agent communication."""
        self.logger.info(
            f"Agent communication {direction}: {other_agent}",
            extra={
                "event_type": f"AGENT_MESSAGE_{direction.upper()}",
                "other_agent": other_agent,
                "comm_message": message,
                "correlation_id": correlation_id
            }
        )
    
    def log_error(self, error: str, error_type: str = "general",
                  correlation_id: Optional[str] = None):
        """Log errors with context."""
        self.logger.error(
            f"Error ({error_type}): {error}",
            extra={
                "event_type": "ERROR",
                "error": error,
                "error_type": error_type,
                "correlation_id": correlation_id
            }
        )
    
    def info(self, message: str, **kwargs):
        """General info logging."""
        self.logger.info(message, extra=kwargs)
    
    def debug(self, message: str, **kwargs):
        """General debug logging."""
        self.logger.debug(message, extra=kwargs)
    
    def warning(self, message: str, **kwargs):
        """General warning logging."""
        self.logger.warning(message, extra=kwargs)
    
    def error(self, message: str, **kwargs):
        """General error logging."""
        self.logger.error(message, extra=kwargs)


def setup_logging(agent_name: str, log_level: str = "INFO", log_file: Optional[str] = None):
    """Set up logging for an agent.
    
    This configures the Python logging system for the agent with:
    - Console output with agent-prefixed formatting
    - Optional file output
    - Specified log level
    """
    # Get root logger for the agent
    logger = logging.getLogger(f"agent.{agent_name}")
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove any existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = AgentLogFormatter(agent_name)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        # Ensure log directory exists
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Don't propagate to root logger
    logger.propagate = False
    
    return logger
