"""Unit tests for AgentMCPClient."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from agent_framework.mcp.client import AgentMCPClient
from agent_framework.core.events import EventStream
from agent_framework.core.logging import AgentLogger


@pytest.fixture
def mock_dependencies():
    """Create mock dependencies for MCP client."""
    event_stream = EventStream(agent_id="test")
    logger = MagicMock(spec=AgentLogger)
    return event_stream, logger


def test_mcp_client_creation(mock_dependencies):
    """Test creating an MCP client."""
    event_stream, logger = mock_dependencies
    
    client = AgentMCPClient(
        agent_id="test_agent",
        event_stream=event_stream,
        logger=logger
    )
    
    assert client.agent_id == "test_agent"
    assert client.connections == {}
    assert client.event_stream == event_stream
    assert client.logger == logger


@pytest.mark.asyncio
async def test_add_connection(mock_dependencies):
    """Test adding a connection to another agent."""
    event_stream, logger = mock_dependencies
    client = AgentMCPClient("test_agent", event_stream, logger)
    
    # Mock fastmcp Client
    with patch('agent_framework.mcp.client.Client') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        # Mock successful connection using context manager
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=None)
        
        # Mock list_tools to return tool objects with name attribute
        mock_tool = MagicMock()
        mock_tool.name = "test_tool"
        mock_client.list_tools = AsyncMock(return_value=[mock_tool])
        
        # Add connection
        success = await client.add_connection("other_agent", "http://localhost:8000/mcp")
        
        assert success is True
        assert "other_agent" in client.connections
        assert client.connections["other_agent"].url == "http://localhost:8000/mcp"
        
        # Verify client was initialized and connected
        mock_client_class.assert_called_once_with("http://localhost:8000/mcp")
        mock_client.__aenter__.assert_called_once()
        mock_client.list_tools.assert_called_once()


@pytest.mark.asyncio
async def test_add_connection_failure(mock_dependencies):
    """Test handling connection failure."""
    event_stream, logger = mock_dependencies
    client = AgentMCPClient("test_agent", event_stream, logger)
    
    with patch('agent_framework.mcp.client.Client') as mock_client_class:
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client
        
        # Mock connection failure
        mock_client.__aenter__ = AsyncMock(side_effect=Exception("Connection failed"))
        
        # Try to add connection
        success = await client.add_connection("other_agent", "http://localhost:8000/mcp")
        
        assert success is False
        # Connection object is created but marked as not connected
        assert "other_agent" in client.connections
        assert not client.connections["other_agent"].connected
        
        # Logger should have been called with error
        logger.log_error.assert_called()


@pytest.mark.asyncio
async def test_call_tool(mock_dependencies):
    """Test calling a tool on a connected server."""
    event_stream, logger = mock_dependencies
    client = AgentMCPClient("test_agent", event_stream, logger)
    
    # Create a mock connection
    mock_connection = MagicMock()
    mock_mcp_client = AsyncMock()
    mock_connection.client = mock_mcp_client
    mock_connection.url = "http://localhost:8000/mcp"
    
    # Mock tool call response
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text='{"result": "success"}')]
    mock_mcp_client.call_tool = AsyncMock(return_value=mock_response)
    
    # Add to connections
    client.connections["other_agent"] = mock_connection
    
    # Call tool
    result = await client.call_tool(
        server_name="other_agent",
        tool_name="test_tool",
        arguments={"input": "test"}
    )
    
    assert result == mock_response
    mock_mcp_client.call_tool.assert_called_once_with(
        "test_tool",
        {"input": "test"}
    )


@pytest.mark.asyncio
async def test_call_tool_not_connected(mock_dependencies):
    """Test calling tool on non-existent connection."""
    event_stream, logger = mock_dependencies
    client = AgentMCPClient("test_agent", event_stream, logger)
    
    # Should return error dict instead of raising exception
    result = await client.call_tool(
        server_name="non_existent",
        tool_name="test_tool",
        arguments={}
    )
    
    assert "error" in result
    assert "No connection to server" in result["error"]


@pytest.mark.asyncio
async def test_communicate_with_agent(mock_dependencies):
    """Test high-level agent communication method."""
    event_stream, logger = mock_dependencies
    client = AgentMCPClient("test_agent", event_stream, logger)
    
    # Mock connection
    mock_conn = MagicMock()
    mock_conn.connected = True
    mock_conn.is_agent = True
    
    # Mock the client's call_tool method
    mock_client = AsyncMock()
    mock_response = {
        "response": "Hello from other agent",
        "conversation_id": "123"
    }
    mock_client.call_tool = AsyncMock(return_value=mock_response)
    mock_conn.client = mock_client
    
    # Add mock connection
    client.connections["other_agent"] = mock_conn
    
    # Communicate
    result = await client.communicate_with_agent(
        target_agent="other_agent",
        message="Hello",
        conversation_id="123"
    )
    
    assert result == mock_response
    mock_client.call_tool.assert_called_once_with(
        "communicate_with_agent",
        {
            "from_agent": "test_agent",
            "message": "Hello",
            "conversation_id": "123"
        }
    )


@pytest.mark.asyncio
async def test_close_all_connections(mock_dependencies):
    """Test closing all connections."""
    event_stream, logger = mock_dependencies
    client = AgentMCPClient("test_agent", event_stream, logger)
    
    # Create mock connections
    mock_conn1 = MagicMock()
    mock_conn1.connected = True
    mock_conn1.client = AsyncMock()
    mock_conn1.client.__aexit__ = AsyncMock()
    
    mock_conn2 = MagicMock()
    mock_conn2.connected = True
    mock_conn2.client = AsyncMock()
    mock_conn2.client.__aexit__ = AsyncMock()
    
    client.connections = {
        "agent1": mock_conn1,
        "agent2": mock_conn2
    }
    
    # Close all
    await client.close_all()
    
    # Verify all connections were closed
    mock_conn1.client.__aexit__.assert_called_once_with(None, None, None)
    mock_conn2.client.__aexit__.assert_called_once_with(None, None, None)
    assert len(client.connections) == 0
