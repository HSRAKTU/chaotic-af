"""Unit tests for CLI connect command."""

import asyncio
import json
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from click.testing import CliRunner

from agent_framework.cli.commands import cli


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


@pytest.fixture
def mock_state():
    """Create mock CLI state with agents."""
    return {
        'agents': {
            'alice': {'pid': 1234, 'port': 8001, 'status': 'running'},
            'bob': {'pid': 5678, 'port': 8002, 'status': 'running'}
        }
    }


@pytest.fixture
def temp_socket_dir():
    """Create temporary socket directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        socket_dir = os.path.join(tmpdir, "chaotic-af")
        os.makedirs(socket_dir)
        # Replace the default socket directory
        original_dir = "/tmp/chaotic-af"
        with patch('agent_framework.cli.commands.connect') as mock_connect:
            # Patch socket paths in the connect function
            yield socket_dir


def test_connect_command_help(runner):
    """Test connect command help."""
    result = runner.invoke(cli, ['connect', '--help'])
    assert result.exit_code == 0
    assert 'Connect agents dynamically' in result.output
    assert '--bidirectional' in result.output


def test_connect_missing_agents(runner, mock_state):
    """Test connect with missing agents."""
    with patch('agent_framework.cli.commands.load_state', return_value={'agents': {}}):
        with patch('agent_framework.cli.commands.save_state'):
            result = runner.invoke(cli, ['connect', 'alice', 'bob'])
            assert result.exit_code == 0
            assert "Agent 'alice' not found" in result.output


def test_connect_socket_not_found(runner, mock_state):
    """Test connect when socket doesn't exist."""
    with patch('agent_framework.cli.commands.load_state', return_value=mock_state):
        with patch('agent_framework.cli.commands.save_state'):
            with patch('os.path.exists', return_value=False):
                result = runner.invoke(cli, ['connect', 'alice', 'bob'])
                assert result.exit_code == 0
                assert "socket not found" in result.output


@pytest.mark.asyncio
async def test_connect_success():
    """Test successful connection via socket."""
    # Create mock socket connection
    mock_reader = AsyncMock()
    mock_writer = AsyncMock()
    
    # Mock successful response
    mock_reader.readline.return_value = json.dumps({'status': 'connected'}).encode() + b'\n'
    
    with patch('asyncio.open_unix_connection', return_value=(mock_reader, mock_writer)):
        with patch('os.path.exists', return_value=True):
            # Import the actual function
            from agent_framework.cli.commands import connect
            
            # Create a mock context
            mock_ctx = MagicMock()
            mock_ctx.obj = {
                'state': {
                    'agents': {
                        'alice': {'pid': 1234, 'port': 8001},
                        'bob': {'pid': 5678, 'port': 8002}
                    }
                }
            }
            
            # Mock click.echo to capture output
            outputs = []
            with patch('click.echo', side_effect=lambda x, **kwargs: outputs.append(x)):
                # Call connect function
                connect(mock_ctx, 'alice', 'bob', False)
            
            # Verify socket connection was made
            mock_writer.write.assert_called_once()
            written_data = mock_writer.write.call_args[0][0]
            cmd = json.loads(written_data.decode().strip())
            
            assert cmd['cmd'] == 'connect'
            assert cmd['target'] == 'bob'
            assert cmd['endpoint'] == 'http://localhost:8002/mcp'
            
            # Check output
            assert any('Connected: alice → bob' in out for out in outputs)


@pytest.mark.asyncio
async def test_connect_bidirectional():
    """Test bidirectional connection."""
    # Create mock socket connections
    mock_reader = AsyncMock()
    mock_writer = AsyncMock()
    
    # Mock successful responses
    mock_reader.readline.return_value = json.dumps({'status': 'connected'}).encode() + b'\n'
    
    call_count = 0
    
    async def mock_connection(*args):
        nonlocal call_count
        call_count += 1
        return mock_reader, mock_writer
    
    with patch('asyncio.open_unix_connection', side_effect=mock_connection):
        with patch('os.path.exists', return_value=True):
            from agent_framework.cli.commands import connect
            
            mock_ctx = MagicMock()
            mock_ctx.obj = {
                'state': {
                    'agents': {
                        'alice': {'pid': 1234, 'port': 8001},
                        'bob': {'pid': 5678, 'port': 8002}
                    }
                }
            }
            
            outputs = []
            with patch('click.echo', side_effect=lambda x, **kwargs: outputs.append(x)):
                connect(mock_ctx, 'alice', 'bob', True)
            
            # Should make 2 connections for bidirectional
            assert call_count == 2
            
            # Check both directions were connected
            assert any('Connected: alice → bob' in out for out in outputs)
            assert any('Connected: bob → alice' in out for out in outputs)
