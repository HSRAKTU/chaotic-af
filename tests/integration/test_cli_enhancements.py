"""Test enhanced CLI commands."""

import pytest
import json
from click.testing import CliRunner
from pathlib import Path
import tempfile
import yaml

from agent_framework.cli.commands import cli


@pytest.fixture
def runner():
    """Create a CLI runner."""
    return CliRunner()


@pytest.fixture
def temp_config():
    """Create a temporary agent configuration file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        config = {
            "agent": {
                "name": "test_cli_agent",
                "llm_provider": "google",
                "llm_model": "gemini-1.5-pro",
                "role_prompt": "Test agent for CLI",
                "port": 8901
            },
            "logging": {
                "level": "INFO",
                "file": "logs/test_cli_agent.log"
            }
        }
        yaml.dump(config, f)
        yield f.name
    
    # Cleanup
    Path(f.name).unlink(missing_ok=True)


def test_health_command_structure(runner):
    """Test the health command structure (without running agent)."""
    
    with runner.isolated_filesystem():
        # Create empty state
        state = {"agents": {}}
        state_file = Path.home() / ".chaotic-af" / "agents.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(state_file, 'w') as f:
            json.dump(state, f)
        
        # Test non-existent agent
        result = runner.invoke(cli, ['health', 'non_existent'])
        assert "✗ Agent 'non_existent' not found" in result.output


def test_metrics_command_structure(runner):
    """Test the metrics command structure."""
    
    with runner.isolated_filesystem():
        # Create empty state
        state = {"agents": {}}
        state_file = Path.home() / ".chaotic-af" / "agents.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(state_file, 'w') as f:
            json.dump(state, f)
        
        # Test non-existent agent
        result = runner.invoke(cli, ['metrics', 'non_existent'])
        assert "✗ Agent 'non_existent' not found" in result.output
        
        # Test format option
        result = runner.invoke(cli, ['metrics', 'non_existent', '-f', 'prometheus'])
        assert "✗ Agent 'non_existent' not found" in result.output


def test_init_command(runner):
    """Test the init command creates a template."""
    
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ['init'])
        assert result.exit_code == 0
        assert "✓ Created agent configuration template" in result.output
        
        # Check file was created
        template_file = Path("agent_template.yaml")
        assert template_file.exists()
        
        # Check content is valid YAML
        with open(template_file) as f:
            config = yaml.safe_load(f)
            assert "agent" in config
            assert config["agent"]["name"] == "my_agent"


@pytest.mark.asyncio
async def test_restart_command(runner, temp_config):
    """Test the restart command."""
    
    # This test is complex because it needs to manage state across restarts
    # For now, we'll just test the command structure
    with runner.isolated_filesystem():
        # Create empty state
        state = {"agents": {}}
        state_file = Path.home() / ".chaotic-af" / "agents.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(state_file, 'w') as f:
            json.dump(state, f)
        
        # Test restart with no agents
        result = runner.invoke(cli, ['restart'])
        assert result.exit_code == 0
        
        # Test restart with non-existent agent
        result = runner.invoke(cli, ['restart', 'non_existent'])
        assert result.exit_code == 0
        assert "⚠ Agent 'non_existent' not found" in result.output


def test_status_command_empty(runner):
    """Test status command with no agents."""
    
    with runner.isolated_filesystem():
        # Create empty state
        state = {"agents": {}}
        state_file = Path.home() / ".chaotic-af" / "agents.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)
        with open(state_file, 'w') as f:
            json.dump(state, f)
        
        result = runner.invoke(cli, ['status'])
        assert result.exit_code == 0
        assert "No agents are currently running" in result.output
