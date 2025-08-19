"""Unit tests for AgentSupervisor."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock
import asyncio
from agent_framework.network.supervisor import AgentSupervisor, AgentProcess
from agent_framework.core.config import AgentConfig


@pytest.fixture
def test_config():
    """Create a test agent configuration."""
    return AgentConfig(
        name="test_agent",
        llm_provider="google",
        llm_model="gemini-1.5-pro",
        role_prompt="Test agent",
        port=9000
    )


def test_supervisor_creation():
    """Test creating a supervisor."""
    supervisor = AgentSupervisor()
    
    assert supervisor.agents == {}
    assert supervisor._monitor_task is None


def test_add_agent(test_config):
    """Test adding an agent to supervisor."""
    supervisor = AgentSupervisor()
    
    supervisor.add_agent(test_config)
    
    assert "test_agent" in supervisor.agents
    agent_proc = supervisor.agents["test_agent"]
    assert isinstance(agent_proc, AgentProcess)
    assert agent_proc.config == test_config
    assert agent_proc.status == "stopped"


@pytest.mark.asyncio
async def test_start_agent_socket_mode(test_config):
    """Test starting an agent with socket mode."""
    supervisor = AgentSupervisor()
    supervisor.add_agent(test_config)
    
    # Mock subprocess
    with patch('agent_framework.network.supervisor.subprocess.Popen') as mock_popen:
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_process.pid = 12345
        mock_popen.return_value = mock_process
        
        # Mock connection manager
        with patch.object(supervisor.connection_manager, 'register_agent') as mock_register:
            success = await supervisor.start_agent("test_agent", monitor_output=False)
            
            assert success is True
            
            # Verify subprocess was started with correct args
            mock_popen.assert_called_once()
            args = mock_popen.call_args[0][0]
            
            # Socket mode is the only mode now
            assert "agent_framework.network.agent_runner" in " ".join(args)
            
            # Verify agent status
            agent_proc = supervisor.agents["test_agent"]
            assert agent_proc.status == "running"
            assert agent_proc.pid == 12345
            
            # Verify registration
            mock_register.assert_called_once_with(
                "test_agent", 
                test_config.port
            )




@pytest.mark.asyncio
async def test_stop_agent(test_config):
    """Test stopping an agent."""
    supervisor = AgentSupervisor()
    supervisor.add_agent(test_config)
    
    # Create mock process
    mock_process = MagicMock()
    mock_process.poll.return_value = None
    mock_process.stdin = MagicMock()
    mock_process.pid = 12345
    
    agent_proc = supervisor.agents["test_agent"]
    agent_proc.process = mock_process
    agent_proc.status = "running"
    agent_proc.pid = 12345
    
    # Mock os functions to avoid actual process operations
    with patch('subprocess.os.kill') as mock_kill:
        # Mock asyncio.sleep to speed up test
        with patch('asyncio.sleep', new_callable=AsyncMock):
            # Mock poll to simulate process still running after SHUTDOWN
            mock_process.poll.side_effect = [None, None, 0]  # Still alive, still alive, then dead
            
            await supervisor.stop_agent("test_agent")
        
        # In socket mode (default), stdin shutdown is not used
        # Should call kill for process termination
        assert mock_kill.called


def test_get_status(test_config):
    """Test getting agent status."""
    supervisor = AgentSupervisor()
    supervisor.add_agent(test_config)
    
    # Set up agent state
    agent_proc = supervisor.agents["test_agent"]
    agent_proc.status = "running"
    agent_proc.pid = 12345
    agent_proc.start_time = 1234567890
    
    status = supervisor.get_status()
    
    assert "test_agent" in status
    assert status["test_agent"]["status"] == "running"
    assert status["test_agent"]["pid"] == 12345
    assert status["test_agent"]["port"] == 9000


@pytest.mark.asyncio
async def test_connect_agents(test_config):
    """Test connecting two agents."""
    supervisor = AgentSupervisor()
    
    # Add two agents
    alice_config = AgentConfig(
        name="alice",
        llm_provider="google",
        llm_model="gemini-1.5-pro",
        role_prompt="Alice",
        port=9001
    )
    bob_config = AgentConfig(
        name="bob",
        llm_provider="google",
        llm_model="gemini-1.5-pro",
        role_prompt="Bob",
        port=9002
    )
    
    supervisor.add_agent(alice_config)
    supervisor.add_agent(bob_config)
    
    # Set agents as running
    supervisor.agents["alice"].status = "running"
    supervisor.agents["bob"].status = "running"
    
    # Mock connection manager
    with patch.object(supervisor.connection_manager, 'connect_agents') as mock_connect:
        mock_connect.return_value = True
        
        await supervisor.connect("alice", "bob", bidirectional=True)
        
        # Should be called twice for bidirectional
        assert mock_connect.call_count == 2
        
        # Check the calls
        calls = mock_connect.call_args_list
        assert calls[0][0] == ("alice", "bob", supervisor.agents)
        assert calls[1][0] == ("bob", "alice", supervisor.agents)
