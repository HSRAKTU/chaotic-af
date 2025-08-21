"""Configuration management for agents.

Requirements:
- Load LLM API keys from .env file
- Parse YAML configuration files for agents
- Provide typed configuration objects
- Support multiple LLM providers
"""

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional, Dict, Any
import yaml
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class AgentConfig:
    """Configuration for a single agent node."""
    name: str
    llm_provider: str  # "openai", "anthropic", "google"
    llm_model: str
    role_prompt: str
    port: int
    external_mcp_servers: List[Dict[str, str]] = field(default_factory=list)
    log_level: str = "INFO"
    log_file: Optional[str] = None
    chaos_mode: bool = False  # Enable agent-to-agent tool calling in communicate_with_agent
    
    def __post_init__(self):
        """Validate configuration."""
        if not self.name:
            raise ValueError("Agent name is required")
        if self.llm_provider not in ["openai", "anthropic", "google"]:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")
        if self.port < 1024 or self.port > 65535:
            raise ValueError(f"Port must be between 1024 and 65535, got {self.port}")


def get_llm_key(provider: str) -> str:
    """Get LLM API key from environment.
    
    Requirements:
    - Support OpenAI, Anthropic, Google API keys
    - Raise clear error if key not found
    """
    key_mapping = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTHROPIC_API_KEY", 
        "google": "GOOGLE_API_KEY"
    }
    
    env_var = key_mapping.get(provider)
    if not env_var:
        raise ValueError(f"Unknown LLM provider: {provider}")
    
    api_key = os.getenv(env_var)
    if not api_key:
        raise ValueError(
            f"Missing API key for {provider}. "
            f"Please set {env_var} in your .env file"
        )
    
    return api_key


def load_config(config_path: str) -> AgentConfig:
    """Load agent configuration from YAML file.
    
    Example YAML:
    ```yaml
    agent:
      name: researcher
      llm_provider: anthropic
      llm_model: claude-3-opus-20240229
      role_prompt: "You are a research assistant..."
      port: 8001
      
    external_mcp_servers:
      - name: web_search
        url: http://localhost:9001/sse
      - name: arxiv
        url: stdio://./tools/arxiv_search.py
        
    logging:
      level: DEBUG
      file: logs/researcher.log
    ```
    """
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(path) as f:
        data = yaml.safe_load(f)
    
    # Extract agent configuration
    agent_data = data.get("agent", {})
    
    # Extract external MCP servers
    external_servers = data.get("external_mcp_servers", [])
    
    # Extract logging configuration
    logging_data = data.get("logging", {})
    
    return AgentConfig(
        name=agent_data["name"],
        llm_provider=agent_data["llm_provider"],
        llm_model=agent_data["llm_model"],
        role_prompt=agent_data["role_prompt"],
        port=agent_data["port"],
        external_mcp_servers=external_servers,
        log_level=logging_data.get("level", "INFO"),
        log_file=logging_data.get("file")
    )
