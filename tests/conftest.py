"""Pytest configuration and shared fixtures."""

import os
import subprocess
import pytest


@pytest.fixture(autouse=True)
def cleanup_agents():
    """Automatically cleanup any running agents before and after tests."""
    # Kill any existing agents before test
    subprocess.run("pkill -f agent_framework.network.agent_runner", 
                   shell=True, capture_output=True)
    
    yield
    
    # Kill any agents after test
    subprocess.run("pkill -f agent_framework.network.agent_runner", 
                   shell=True, capture_output=True)
    
    # Clean up socket directory
    socket_dir = "/tmp/chaotic-af"
    if os.path.exists(socket_dir):
        for sock_file in os.listdir(socket_dir):
            if sock_file.endswith('.sock'):
                try:
                    os.unlink(os.path.join(socket_dir, sock_file))
                except:
                    pass
