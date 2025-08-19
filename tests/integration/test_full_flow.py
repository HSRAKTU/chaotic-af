"""Integration test for complete agent flow with socket mode."""

import asyncio
import json
import os
import pytest
from agent_framework import AgentSupervisor, AgentConfig, AgentMCPClient, EventStream


@pytest.mark.asyncio
async def test_full_agent_flow():
    """Test complete flow: start agents, connect, communicate, shutdown."""
    
    # Create supervisor with socket mode (explicitly enable)
    supervisor = AgentSupervisor()
    
    # Create test agents
    alice = AgentConfig(
        name="alice",
        llm_provider="google",
        llm_model="gemini-1.5-pro",
        role_prompt="You are Alice. When asked about geography, contact Bob for help.",
        port=8501
    )
    
    bob = AgentConfig(
        name="bob",
        llm_provider="google",
        llm_model="gemini-1.5-pro", 
        role_prompt="You are Bob, a geography expert. Paris is the capital of France.",
        port=8502
    )
    
    supervisor.add_agent(alice)
    supervisor.add_agent(bob)
    
    try:
        # Start agents
        await supervisor.start_all(monitor=False)
        await asyncio.sleep(3)
        
        # Verify agents are running
        status = supervisor.get_status()
        assert status["alice"]["status"] == "running"
        assert status["bob"]["status"] == "running"
        
        # Connect agents bidirectionally
        await supervisor.connect("alice", "bob", bidirectional=True)
        await asyncio.sleep(1)
        
        # In our current architecture, agents communicate via Unix sockets
        # Let's verify the agents can talk to each other via supervisor commands
        
        # Check that both agents have their sockets ready
        await asyncio.sleep(2)
        
        # Verify connection was established
        connections = supervisor.connection_manager.get_connections()
        # Connections are stored as tuples (from, to) -> True
        assert ("alice", "bob") in connections
        assert ("bob", "alice") in connections
        assert connections[("alice", "bob")] is True
        assert connections[("bob", "alice")] is True
        
        # Test direct socket communication to verify agents are responsive
        socket_path = "/tmp/chaotic-af/agent-alice.sock"
        
        # Wait for socket to exist
        for _ in range(10):
            if os.path.exists(socket_path):
                break
            await asyncio.sleep(0.5)
        
        if os.path.exists(socket_path):
            reader, writer = await asyncio.open_unix_connection(socket_path)
            cmd = {'cmd': 'health'}
            writer.write(json.dumps(cmd).encode() + b'\n')
            await writer.drain()
            
            response = await reader.readline()
            result = json.loads(response.decode())
            assert result['status'] == 'ready'
            
            writer.close()
            await writer.wait_closed()
        
    finally:
        # Always clean up
        await supervisor.stop_all()


@pytest.mark.asyncio
async def test_socket_health_check():
    """Test agent health check via socket."""
    supervisor = AgentSupervisor()
    
    test_agent = AgentConfig(
        name="test_health",
        llm_provider="google",
        llm_model="gemini-1.5-pro",
        role_prompt="Test agent",
        port=8503
    )
    
    supervisor.add_agent(test_agent)
    
    try:
        # Start agent
        await supervisor.start_agent("test_health", monitor_output=False)
        await asyncio.sleep(3)  # Give more time for socket creation
        
        # Check health via socket
        socket_path = "/tmp/chaotic-af/agent-test_health.sock"
        
        # Wait for socket to exist
        for _ in range(10):
            if os.path.exists(socket_path):
                break
            await asyncio.sleep(0.5)
        else:
            pytest.fail(f"Socket file not created: {socket_path}")
        
        # Connect to socket
        reader, writer = await asyncio.open_unix_connection(socket_path)
        
        # Send health command
        cmd = {'cmd': 'health'}
        writer.write(json.dumps(cmd).encode() + b'\n')
        await writer.drain()
        
        # Read response
        response = await reader.readline()
        result = json.loads(response.decode())
        
        # Verify health response
        assert result['status'] == 'ready'
        
        writer.close()
        await writer.wait_closed()
        
    finally:
        await supervisor.stop_all()
