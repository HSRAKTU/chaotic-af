"""Unit tests for AgentSupervisor."""

import pytest
from unittest.mock import MagicMock, patch, AsyncMock, call
import asyncio
import subprocess
import os
import signal
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
            assert agent_proc.status == "starting"  # Initially starting, becomes running when socket ready
            assert agent_proc.pid == 12345
            
            # Verify registration
            mock_register.assert_called_once_with(
                "test_agent", 
                test_config.port
            )
            
            # Verify DEVNULL is used when monitor_output=False
            kwargs = mock_popen.call_args[1]
            assert kwargs['stdout'] == subprocess.DEVNULL
            assert kwargs['stderr'] == subprocess.DEVNULL




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


@pytest.mark.asyncio
async def test_start_all_non_blocking(test_config):
    """Test start_all with wait_ready=False for non-blocking behavior."""
    supervisor = AgentSupervisor()
    
    # Add multiple agents
    configs = []
    for i in range(3):
        config = AgentConfig(
            name=f"agent_{i}",
            llm_provider="google",
            llm_model="gemini-1.5-pro",
            role_prompt=f"Agent {i}",
            port=9000 + i
        )
        configs.append(config)
        supervisor.add_agent(config)
    
    with patch('agent_framework.network.supervisor.subprocess.Popen') as mock_popen:
        # Create mock processes
        mock_processes = []
        for i in range(3):
            mock_process = MagicMock()
            mock_process.poll.return_value = None
            mock_process.pid = 12345 + i
            mock_processes.append(mock_process)
        
        mock_popen.side_effect = mock_processes
        
        # Test non-blocking start
        with patch('asyncio.sleep', new_callable=AsyncMock):
            await supervisor.start_all(monitor=False, wait_ready=False)
        
        # All agents should be in "starting" status
        for i in range(3):
            agent_proc = supervisor.agents[f"agent_{i}"]
            assert agent_proc.status == "starting"
            assert agent_proc.pid == 12345 + i
        
        # Verify that _wait_for_all_ready was NOT called
        # (This would be tested by checking that the function returns quickly)


@pytest.mark.asyncio
async def test_start_agent_with_monitoring(test_config):
    """Test starting an agent with output monitoring enabled."""
    supervisor = AgentSupervisor()
    supervisor.add_agent(test_config)
    
    with patch('agent_framework.network.supervisor.subprocess.Popen') as mock_popen:
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_process.pid = 12345
        mock_process.stdout = MagicMock()
        mock_process.stderr = MagicMock()
        mock_popen.return_value = mock_process
        
        with patch.object(supervisor.connection_manager, 'register_agent'):
            # Start with monitoring enabled
            success = await supervisor.start_agent("test_agent", monitor_output=True)
            
            assert success is True
            
            # Verify PIPE is used when monitor_output=True
            kwargs = mock_popen.call_args[1]
            assert kwargs['stdout'] == subprocess.PIPE
            assert kwargs['stderr'] == subprocess.PIPE


@pytest.mark.asyncio
async def test_socket_based_shutdown(test_config):
    """Test agent shutdown via socket command."""
    supervisor = AgentSupervisor()
    supervisor.add_agent(test_config)
    
    # Set up running agent
    agent_proc = supervisor.agents["test_agent"]
    agent_proc.status = "running"
    agent_proc.pid = 12345
    
    mock_process = MagicMock()
    mock_process.poll.return_value = None
    agent_proc.process = mock_process
    
    # Mock socket connection
    with patch('os.path.exists', return_value=True):
        mock_reader = AsyncMock()
        mock_writer = MagicMock()  # Use MagicMock for writer, not AsyncMock
        # Mock async methods
        mock_writer.drain = AsyncMock()
        mock_writer.wait_closed = AsyncMock()
        mock_reader.readline.return_value = b'{"status": "ok"}\n'
        
        with patch('asyncio.open_unix_connection', return_value=(mock_reader, mock_writer)):
            with patch('asyncio.sleep', new_callable=AsyncMock):
                with patch('subprocess.os.kill') as mock_kill:
                    # First poll returns None (process running), then 0 (process stopped)
                    mock_process.poll.side_effect = [None, 0]
                    
                    await supervisor.stop_agent("test_agent")
                    
                    # Verify socket command was sent
                    mock_writer.write.assert_called()
                    sent_data = mock_writer.write.call_args[0][0]
                    assert b'"cmd": "shutdown"' in sent_data
                    
                    # Process should receive SIGTERM for clean shutdown
                    mock_kill.assert_called_once_with(12345, signal.SIGTERM)


@pytest.mark.asyncio
async def test_status_transitions():
    """Test agent status transitions from starting to running."""
    supervisor = AgentSupervisor()
    
    config = AgentConfig(
        name="transition_test",
        llm_provider="google",
        llm_model="gemini-1.5-pro",
        role_prompt="Test",
        port=9000
    )
    supervisor.add_agent(config)
    
    # Initially stopped
    agent_proc = supervisor.agents["transition_test"]
    assert agent_proc.status == "stopped"
    
    # Start agent
    with patch('agent_framework.network.supervisor.subprocess.Popen') as mock_popen:
        mock_process = MagicMock()
        mock_process.poll.return_value = None
        mock_process.pid = 12345
        mock_popen.return_value = mock_process
        
        with patch.object(supervisor.connection_manager, 'register_agent'):
            await supervisor.start_agent("transition_test", monitor_output=False)
    
    # Should be starting
    assert agent_proc.status == "starting"
    
    # Simulate READY signal
    agent_proc.is_ready = True
    agent_proc.status = "running"
    
    # Should be running
    assert agent_proc.status == "running"
    
    # Simulate crash
    agent_proc.process.poll.return_value = 1
    agent_proc.status = "failed"
    
    assert agent_proc.status == "failed"
