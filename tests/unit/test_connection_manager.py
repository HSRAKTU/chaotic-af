"""Unit tests for ConnectionManager."""

import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from agent_framework.network.connection_manager import ConnectionManager


def test_connection_manager_creation():
    """Test creating a connection manager."""
    manager = ConnectionManager()
    
    assert manager.agent_registry == {}
    assert manager.connections == {}


def test_register_agent():
    """Test registering an agent."""
    manager = ConnectionManager()
    
    # Register agent
    manager.register_agent("alice", 8001)
    
    assert "alice" in manager.agent_registry
    assert manager.agent_registry["alice"] == 8001


def test_get_agent_endpoint():
    """Test getting agent endpoint."""
    manager = ConnectionManager()
    
    # Register agent
    manager.register_agent("alice", 8001)
    
    # Get endpoint
    endpoint = manager.get_agent_endpoint("alice")
    assert endpoint == "http://localhost:8001/mcp"
    
    # Non-existent agent
    endpoint = manager.get_agent_endpoint("non-existent")
    assert endpoint is None


@pytest.mark.asyncio
async def test_connect_agents_via_socket():
    """Test connecting agents via socket."""
    manager = ConnectionManager()
    
    # Register agents
    manager.register_agent("alice", 8001)
    manager.register_agent("bob", 8002)
    
    # Create mock agent processes
    mock_agent_procs = {
        "alice": MagicMock(process=MagicMock(stdin=MagicMock())),
        "bob": MagicMock(process=MagicMock(stdin=MagicMock()))
    }
    
    # Mock socket connection
    with patch('asyncio.open_unix_connection') as mock_open_socket:
        mock_reader = AsyncMock()
        mock_writer = MagicMock()  # Use regular mock for writer methods that aren't async
        mock_writer.write = MagicMock(return_value=None)
        mock_writer.drain = AsyncMock()
        mock_writer.close = MagicMock(return_value=None)
        mock_writer.wait_closed = AsyncMock()
        mock_reader.readline.return_value = b'{"status": "connected"}\n'
        mock_open_socket.return_value = (mock_reader, mock_writer)
        
        # Mock os.path.exists to return True for socket
        with patch('os.path.exists', return_value=True):
            success = await manager.connect_agents("alice", "bob", mock_agent_procs)
            
            assert success is True
            assert ("alice", "bob") in manager.connections
            
            # Verify socket was used
            mock_open_socket.assert_called_once_with("/tmp/chaotic-af/agent-alice.sock")
            
            # Verify correct command was sent
            mock_writer.write.assert_called_once()
            sent_data = mock_writer.write.call_args[0][0]
            assert b'"cmd": "connect"' in sent_data
            assert b'"target": "bob"' in sent_data
            assert b'"endpoint": "http://localhost:8002/mcp"' in sent_data





@pytest.mark.asyncio
async def test_connect_unknown_agents():
    """Test connecting unknown agents."""
    manager = ConnectionManager()
    
    # Only register alice
    manager.register_agent("alice", 8001)
    
    mock_agent_procs = {
        "alice": MagicMock()
    }
    
    # Try to connect to unregistered agent
    success = await manager.connect_agents("alice", "unknown", mock_agent_procs)
    assert success is False
    assert ("alice", "unknown") not in manager.connections
    
    # Try from unregistered agent
    success = await manager.connect_agents("unknown", "alice", {"alice": MagicMock()})
    assert success is False


def test_get_connections():
    """Test getting all connections."""
    manager = ConnectionManager()
    
    # Add some connections
    manager.connections[("alice", "bob")] = True
    manager.connections[("bob", "charlie")] = True
    
    connections = manager.get_connections()
    
    assert len(connections) == 2
    assert ("alice", "bob") in connections
    assert ("bob", "charlie") in connections


def test_is_connected():
    """Test checking if agents are connected."""
    manager = ConnectionManager()
    
    # Add connection
    manager.connections[("alice", "bob")] = True
    
    assert manager.is_connected("alice", "bob") is True
    assert manager.is_connected("bob", "alice") is False  # Not bidirectional
    assert manager.is_connected("alice", "charlie") is False
