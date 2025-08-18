"""Unit tests for AgentConfig."""

import pytest
from agent_framework.core.config import AgentConfig, load_config
import tempfile
import yaml
import os


def test_agent_config_creation():
    """Test creating an AgentConfig."""
    config = AgentConfig(
        name="test_agent",
        llm_provider="openai",
        llm_model="gpt-4",
        role_prompt="Test agent",
        port=8000
    )
    
    assert config.name == "test_agent"
    assert config.llm_provider == "openai"
    assert config.llm_model == "gpt-4"
    assert config.role_prompt == "Test agent"
    assert config.port == 8000
    assert config.log_level == "INFO"  # default
    assert config.external_mcp_servers == []  # default


def test_agent_config_direct_creation():
    """Test creating AgentConfig directly from parameters."""
    config = AgentConfig(
        name="alice",
        llm_provider="google",
        llm_model="gemini-1.5-pro",
        role_prompt="You are Alice",
        port=8001,
        log_level="DEBUG"
    )
    
    assert config.name == "alice"
    assert config.llm_provider == "google"
    assert config.llm_model == "gemini-1.5-pro"
    assert config.role_prompt == "You are Alice"
    assert config.port == 8001
    assert config.log_level == "DEBUG"


def test_load_config_from_file():
    """Test loading config from YAML file."""
    yaml_content = """
agent:
  name: bob
  llm_provider: anthropic
  llm_model: claude-3-opus
  role_prompt: |
    You are Bob.
    You help with various tasks.
  port: 8002

external_mcp_servers:
  - name: calculator
    url: http://localhost:9000/mcp

logging:
  level: DEBUG
  file: logs/bob.log
"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(yaml_content)
        f.flush()
        temp_path = f.name
        
    try:
        config = load_config(temp_path)
        
        assert config.name == "bob"
        assert config.llm_provider == "anthropic"
        assert config.llm_model == "claude-3-opus"
        assert "You are Bob" in config.role_prompt
        assert config.port == 8002
        assert len(config.external_mcp_servers) == 1
        assert config.external_mcp_servers[0]["name"] == "calculator"
        assert config.log_level == "DEBUG"
        assert config.log_file == "logs/bob.log"
    finally:
        os.unlink(temp_path)


def test_config_validation():
    """Test config validation."""
    # Missing required fields should raise error
    with pytest.raises(TypeError):
        AgentConfig(name="test")  # Missing required fields
        
    # Invalid provider should raise ValueError
    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        AgentConfig(
            name="test",
            llm_provider="invalid_provider",
            llm_model="model",
            role_prompt="prompt",
            port=8000
        )
    
    # Invalid port should raise ValueError
    with pytest.raises(ValueError, match="Port must be between"):
        AgentConfig(
            name="test",
            llm_provider="openai",
            llm_model="gpt-4",
            role_prompt="prompt",
            port=999  # Too low
        )
