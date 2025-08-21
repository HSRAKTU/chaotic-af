"""Unit tests for AgentSocketClient."""

import asyncio
import json
import os
import tempfile
from unittest.mock import patch, MagicMock, AsyncMock
import pytest

from agent_framework.client.socket_client import AgentSocketClient


@pytest.mark.asyncio
async def test_send_command_success():
    """Test successful command sending."""
    # Mock reader and writer
    mock_reader = AsyncMock()
    mock_writer = MagicMock()
    mock_writer.drain = AsyncMock()
    mock_writer.wait_closed = AsyncMock()
    mock_reader.readline.return_value = json.dumps({"status": "ok"}).encode() + b'\n'
    
    with patch('os.path.exists', return_value=True):
        with patch('asyncio.open_unix_connection', return_value=(mock_reader, mock_writer)):
            result = await AgentSocketClient.send_command("test_agent", {"cmd": "health"})
            
            assert result == {"status": "ok"}
            mock_writer.write.assert_called_once()
            mock_writer.drain.assert_called_once()
            mock_writer.close.assert_called_once()


@pytest.mark.asyncio
async def test_send_command_socket_not_found():
    """Test when socket doesn't exist."""
    with patch('os.path.exists', return_value=False):
        result = await AgentSocketClient.send_command("test_agent", {"cmd": "health"})
        assert result == {"error": "Socket not found for agent test_agent"}


@pytest.mark.asyncio
async def test_send_command_timeout():
    """Test timeout handling."""
    with patch('os.path.exists', return_value=True):
        with patch('asyncio.open_unix_connection', side_effect=asyncio.TimeoutError):
            result = await AgentSocketClient.send_command("test_agent", {"cmd": "health"}, timeout=0.1)
            assert result == {"error": "Timeout connecting to test_agent"}


@pytest.mark.asyncio
async def test_send_command_exception():
    """Test general exception handling."""
    with patch('os.path.exists', return_value=True):
        with patch('asyncio.open_unix_connection', side_effect=Exception("Connection failed")):
            result = await AgentSocketClient.send_command("test_agent", {"cmd": "health"})
            assert "Failed to communicate with test_agent" in result["error"]
            assert "Connection failed" in result["error"]


@pytest.mark.asyncio
async def test_health_check():
    """Test health check convenience method."""
    mock_reader = AsyncMock()
    mock_writer = MagicMock()
    mock_writer.drain = AsyncMock()
    mock_writer.wait_closed = AsyncMock()
    mock_reader.readline.return_value = json.dumps({"status": "ready"}).encode() + b'\n'
    
    with patch('os.path.exists', return_value=True):
        with patch('asyncio.open_unix_connection', return_value=(mock_reader, mock_writer)):
            result = await AgentSocketClient.health_check("test_agent")
            assert result == {"status": "ready"}


@pytest.mark.asyncio
async def test_connect_agents():
    """Test connect agents convenience method."""
    mock_reader = AsyncMock()
    mock_writer = MagicMock()
    mock_writer.drain = AsyncMock()
    mock_writer.wait_closed = AsyncMock()
    mock_reader.readline.return_value = json.dumps({"status": "connected"}).encode() + b'\n'
    
    with patch('os.path.exists', return_value=True):
        with patch('asyncio.open_unix_connection', return_value=(mock_reader, mock_writer)):
            result = await AgentSocketClient.connect_agents(
                "alice", "bob", "http://localhost:8002/mcp"
            )
            assert result == {"status": "connected"}
            
            # Verify the command sent
            sent_data = mock_writer.write.call_args[0][0]
            sent_cmd = json.loads(sent_data.decode().strip())
            assert sent_cmd["cmd"] == "connect"
            assert sent_cmd["target"] == "bob"
            assert sent_cmd["endpoint"] == "http://localhost:8002/mcp"


@pytest.mark.asyncio
async def test_shutdown_agent():
    """Test shutdown agent convenience method."""
    mock_reader = AsyncMock()
    mock_writer = MagicMock()
    mock_writer.drain = AsyncMock()
    mock_writer.wait_closed = AsyncMock()
    mock_reader.readline.return_value = json.dumps({"status": "shutting_down"}).encode() + b'\n'
    
    with patch('os.path.exists', return_value=True):
        with patch('asyncio.open_unix_connection', return_value=(mock_reader, mock_writer)):
            result = await AgentSocketClient.shutdown_agent("test_agent")
            assert result == {"status": "shutting_down"}


@pytest.mark.asyncio
async def test_get_metrics():
    """Test get metrics convenience method."""
    mock_reader = AsyncMock()
    mock_writer = MagicMock()
    mock_writer.drain = AsyncMock()
    mock_writer.wait_closed = AsyncMock()
    mock_reader.readline.return_value = json.dumps({
        "metrics": {"counters": {}, "gauges": {}}
    }).encode() + b'\n'
    
    with patch('os.path.exists', return_value=True):
        with patch('asyncio.open_unix_connection', return_value=(mock_reader, mock_writer)):
            result = await AgentSocketClient.get_metrics("test_agent", "json")
            assert "metrics" in result
            
            # Verify format parameter
            sent_data = mock_writer.write.call_args[0][0]
            sent_cmd = json.loads(sent_data.decode().strip())
            assert sent_cmd["format"] == "json"
