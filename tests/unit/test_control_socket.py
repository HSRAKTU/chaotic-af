"""Unit tests for AgentControlSocket."""

import asyncio
import json
import os
import tempfile
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock

from agent_framework.network.control_socket import AgentControlSocket


@pytest.fixture
def mock_agent():
    """Create a mock agent for testing."""
    agent = MagicMock()
    agent.mcp_client = AsyncMock()
    agent.mcp_server = MagicMock()
    agent._shutdown_event = asyncio.Event()
    return agent


@pytest_asyncio.fixture
async def socket_server(mock_agent):
    """Create a control socket server for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        socket_path = os.path.join(tmpdir, "test.sock")
        control = AgentControlSocket(mock_agent, socket_path)
        server = await control.start()
        
        # Start server in background
        server_task = asyncio.create_task(server.serve_forever())
        
        yield control, socket_path
        
        # Cleanup
        server.close()
        await server.wait_closed()
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass


@pytest.mark.asyncio
async def test_socket_creation(socket_server):
    """Test that socket file is created."""
    control, socket_path = socket_server
    assert os.path.exists(socket_path)


@pytest.mark.asyncio
async def test_health_command(socket_server):
    """Test health check command."""
    control, socket_path = socket_server
    
    # Connect to socket
    reader, writer = await asyncio.open_unix_connection(socket_path)
    
    # Send health command
    cmd = {'cmd': 'health'}
    writer.write(json.dumps(cmd).encode() + b'\n')
    await writer.drain()
    
    # Read response
    response = await reader.readline()
    result = json.loads(response.decode())
    
    assert result['status'] == 'ready'
    
    writer.close()
    await writer.wait_closed()


@pytest.mark.asyncio
async def test_connect_command(socket_server, mock_agent):
    """Test connect command."""
    control, socket_path = socket_server
    
    # Mock successful connection
    mock_agent.mcp_client.add_connection.return_value = True
    mock_agent.mcp_client.connections = {'bob': 'connection'}
    
    # Connect to socket
    reader, writer = await asyncio.open_unix_connection(socket_path)
    
    # Send connect command
    cmd = {
        'cmd': 'connect',
        'target': 'bob',
        'endpoint': 'http://localhost:8002/mcp'
    }
    writer.write(json.dumps(cmd).encode() + b'\n')
    await writer.drain()
    
    # Read response
    response = await reader.readline()
    result = json.loads(response.decode())
    
    assert result['status'] == 'connected'
    mock_agent.mcp_client.add_connection.assert_called_once_with(
        'bob', 'http://localhost:8002/mcp'
    )
    
    writer.close()
    await writer.wait_closed()


@pytest.mark.asyncio
async def test_shutdown_command(socket_server, mock_agent):
    """Test shutdown command."""
    control, socket_path = socket_server
    
    # Connect to socket
    reader, writer = await asyncio.open_unix_connection(socket_path)
    
    # Send shutdown command
    cmd = {'cmd': 'shutdown'}
    writer.write(json.dumps(cmd).encode() + b'\n')
    await writer.drain()
    
    # Read response
    response = await reader.readline()
    result = json.loads(response.decode())
    
    assert result['status'] == 'shutting_down'
    assert mock_agent._shutdown_event.is_set()
    
    writer.close()
    await writer.wait_closed()


@pytest.mark.asyncio
async def test_unknown_command(socket_server):
    """Test handling of unknown command."""
    control, socket_path = socket_server
    
    # Connect to socket
    reader, writer = await asyncio.open_unix_connection(socket_path)
    
    # Send unknown command
    cmd = {'cmd': 'unknown'}
    writer.write(json.dumps(cmd).encode() + b'\n')
    await writer.drain()
    
    # Read response
    response = await reader.readline()
    result = json.loads(response.decode())
    
    assert 'error' in result
    assert 'Unknown command' in result['error']
    
    writer.close()
    await writer.wait_closed()


@pytest.mark.asyncio
async def test_malformed_json(socket_server):
    """Test handling of malformed JSON."""
    control, socket_path = socket_server
    
    # Connect to socket
    reader, writer = await asyncio.open_unix_connection(socket_path)
    
    # Send malformed JSON
    writer.write(b'not json\n')
    await writer.drain()
    
    # Read response
    response = await reader.readline()
    result = json.loads(response.decode())
    
    assert 'error' in result
    
    writer.close()
    await writer.wait_closed()


@pytest.mark.asyncio
async def test_multiple_connections(socket_server):
    """Test handling multiple simultaneous connections."""
    control, socket_path = socket_server
    
    # Create multiple connections
    connections = []
    for i in range(3):
        reader, writer = await asyncio.open_unix_connection(socket_path)
        connections.append((reader, writer))
    
    # Send health command from each
    for reader, writer in connections:
        cmd = {'cmd': 'health'}
        writer.write(json.dumps(cmd).encode() + b'\n')
        await writer.drain()
    
    # Read responses
    for reader, writer in connections:
        response = await reader.readline()
        result = json.loads(response.decode())
        assert result['status'] == 'ready'
        
        writer.close()
        await writer.wait_closed()
