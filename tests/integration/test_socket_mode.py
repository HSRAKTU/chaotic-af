"""Integration tests for socket mode."""

import asyncio
import json
import os
import time
import psutil
import pytest
import pytest_asyncio
from agent_framework import AgentSupervisor, AgentConfig


@pytest_asyncio.fixture
async def supervisor():
    """Create a supervisor with socket mode enabled."""
    supervisor = AgentSupervisor()
    supervisor.use_sockets = True
    yield supervisor
    # Cleanup
    await supervisor.stop_all()


@pytest.fixture
def alice_config():
    """Create Alice agent config."""
    return AgentConfig(
        name="alice",
        llm_provider="google",
        llm_model="gemini-1.5-pro",
        role_prompt="You are Alice, a helpful assistant.",
        port=8101  # Use different ports to avoid conflicts
    )


@pytest.fixture
def bob_config():
    """Create Bob agent config."""
    return AgentConfig(
        name="bob",
        llm_provider="google",
        llm_model="gemini-1.5-pro",
        role_prompt="You are Bob, a knowledgeable assistant.",
        port=8102
    )


@pytest.mark.asyncio
async def test_agent_startup_with_sockets(supervisor, alice_config):
    """Test that agents start correctly in socket mode."""
    supervisor.add_agent(alice_config)
    
    # Start agent
    success = await supervisor.start_agent("alice", monitor_output=False)
    assert success
    
    # Wait for socket to be created
    await asyncio.sleep(2)
    
    # Check socket exists
    socket_path = f"/tmp/chaotic-af/agent-alice.sock"
    assert os.path.exists(socket_path)
    
    # Check agent is running
    status = supervisor.get_status()
    assert status["alice"]["status"] == "running"


@pytest.mark.asyncio
async def test_cpu_usage_with_sockets(supervisor, alice_config):
    """Test that CPU usage is low in socket mode."""
    supervisor.add_agent(alice_config)
    
    # Start agent
    await supervisor.start_agent("alice", monitor_output=False)
    await asyncio.sleep(2)
    
    # Get agent process
    agent_proc = supervisor.agents["alice"]
    assert agent_proc.process is not None
    
    # Monitor CPU for a few seconds
    proc = psutil.Process(agent_proc.pid)
    cpu_percent = proc.cpu_percent(interval=3.0)
    
    # CPU should be very low (< 5%)
    assert cpu_percent < 5.0, f"CPU usage too high: {cpu_percent}%"


@pytest.mark.asyncio
async def test_socket_connection(supervisor, alice_config, bob_config):
    """Test connecting agents via sockets."""
    supervisor.add_agent(alice_config)
    supervisor.add_agent(bob_config)
    
    # Start both agents
    await supervisor.start_all(monitor=False)
    await asyncio.sleep(3)
    
    # Connect alice -> bob
    await supervisor.connect("alice", "bob")
    
    # Verify connection via socket
    socket_path = f"/tmp/chaotic-af/agent-alice.sock"
    reader, writer = await asyncio.open_unix_connection(socket_path)
    
    # Check health (should include connections)
    cmd = {'cmd': 'health'}
    writer.write(json.dumps(cmd).encode() + b'\n')
    await writer.drain()
    
    response = await reader.readline()
    result = json.loads(response.decode())
    
    assert result['status'] == 'ready'
    # Note: connections info would need to be added to health response
    
    writer.close()
    await writer.wait_closed()


@pytest.mark.asyncio
async def test_socket_shutdown(supervisor, alice_config):
    """Test shutting down agent via socket."""
    supervisor.add_agent(alice_config)
    
    # Start agent
    await supervisor.start_agent("alice", monitor_output=False)
    await asyncio.sleep(2)
    
    # Send shutdown via socket
    socket_path = f"/tmp/chaotic-af/agent-alice.sock"
    reader, writer = await asyncio.open_unix_connection(socket_path)
    
    cmd = {'cmd': 'shutdown'}
    writer.write(json.dumps(cmd).encode() + b'\n')
    await writer.drain()
    
    response = await reader.readline()
    result = json.loads(response.decode())
    assert result['status'] == 'shutting_down'
    
    writer.close()
    await writer.wait_closed()
    
    # Wait for shutdown
    await asyncio.sleep(2)
    
    # Check agent stopped
    status = supervisor.get_status()
    assert "alice" not in status or status["alice"]["status"] != "running"


@pytest.mark.asyncio
async def test_backward_compatibility(supervisor, alice_config, bob_config):
    """Test that stdin mode still works when sockets disabled."""
    # Disable sockets
    supervisor.use_sockets = False
    
    supervisor.add_agent(alice_config)
    supervisor.add_agent(bob_config)
    
    # Start agents (will use stdin)
    await supervisor.start_all(monitor=False)
    await asyncio.sleep(3)
    
    # Agents should be running
    status = supervisor.get_status()
    assert status["alice"]["status"] == "running"
    assert status["bob"]["status"] == "running"
    
    # Socket files should NOT exist
    assert not os.path.exists("/tmp/chaotic-af/agent-alice.sock")
    assert not os.path.exists("/tmp/chaotic-af/agent-bob.sock")
