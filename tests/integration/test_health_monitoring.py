"""Test health monitoring and auto-recovery functionality."""

import asyncio
import pytest
import os
import signal
from agent_framework import AgentSupervisor, AgentConfig
from agent_framework.core.health import HealthConfig


@pytest.mark.asyncio
async def test_health_monitoring_basic():
    """Test basic health monitoring functionality."""
    
    # Create supervisor with custom health config
    health_config = HealthConfig(
        check_interval=2.0,  # Check every 2 seconds
        failure_threshold=2,  # 2 failures before restart
        restart_delay=1.0
    )
    supervisor = AgentSupervisor(use_sockets=True, health_config=health_config)
    
    # Create test agent
    test_agent = AgentConfig(
        name="health_test",
        llm_provider="google",
        llm_model="gemini-1.5-pro",
        role_prompt="Test agent for health monitoring",
        port=8701
    )
    
    supervisor.add_agent(test_agent)
    
    try:
        # Start agent with monitoring
        await supervisor.start_all(monitor=True)
        await asyncio.sleep(3)
        
        # Verify agent is running
        status = supervisor.get_status()
        assert status["health_test"]["status"] == "running"
        
        # Get initial health status
        health_status = supervisor.get_health_status()
        assert "health_test" in health_status
        assert health_status["health_test"]["healthy"] is True
        assert health_status["health_test"]["consecutive_failures"] == 0
        
        # Wait for a couple health checks
        await asyncio.sleep(5)
        
        # Verify health checks are happening
        health_status = supervisor.get_health_status()
        assert health_status["health_test"]["healthy"] is True
        
    finally:
        await supervisor.stop_all()


@pytest.mark.asyncio
async def test_auto_recovery():
    """Test that agents are automatically restarted when they crash."""
    
    # Create supervisor with aggressive health config
    health_config = HealthConfig(
        check_interval=1.0,  # Check every second
        failure_threshold=2,  # 2 failures before restart
        restart_delay=0.5
    )
    supervisor = AgentSupervisor(use_sockets=True, health_config=health_config)
    
    # Create test agent
    test_agent = AgentConfig(
        name="crash_test",
        llm_provider="google",
        llm_model="gemini-1.5-pro",
        role_prompt="Test agent that will crash",
        port=8702
    )
    
    supervisor.add_agent(test_agent)
    
    try:
        # Start agent
        await supervisor.start_all(monitor=True)
        await asyncio.sleep(2)
        
        # Get initial PID
        status = supervisor.get_status()
        original_pid = status["crash_test"]["pid"]
        assert original_pid is not None
        
        # Kill the agent process to simulate crash
        os.kill(original_pid, signal.SIGKILL)
        
        # Wait for health monitor to detect and restart
        # Health check interval is 1s, failure threshold is 2, so detection takes ~2s
        # Then restart delay is 0.5s, agent startup takes ~2s, socket wait takes up to 5s
        # Total recovery time could be up to 10 seconds
        await asyncio.sleep(10)
        
        # Verify agent was restarted with new PID
        status = supervisor.get_status()
        new_pid = status["crash_test"]["pid"]
        assert new_pid is not None
        assert new_pid != original_pid
        assert status["crash_test"]["status"] == "running"
        
        # Check health status shows recovery
        health_status = supervisor.get_health_status()
        assert health_status["crash_test"]["healthy"] is True
        
    finally:
        await supervisor.stop_all()


@pytest.mark.asyncio
async def test_restart_limit():
    """Test that restart limits are enforced."""
    
    # Create supervisor with low restart limit
    health_config = HealthConfig(
        check_interval=0.5,
        failure_threshold=1,
        restart_delay=0.1,
        max_restarts=2  # Only allow 2 restarts
    )
    supervisor = AgentSupervisor(use_sockets=True, health_config=health_config)
    
    # Create test agent
    test_agent = AgentConfig(
        name="limit_test",
        llm_provider="google",
        llm_model="gemini-1.5-pro",
        role_prompt="Test agent for restart limits",
        port=8703
    )
    
    supervisor.add_agent(test_agent)
    
    try:
        # Start agent
        await supervisor.start_all(monitor=True)
        await asyncio.sleep(2)
        
        # Kill agent multiple times to exceed limit
        # We expect: original -> restart 1 -> restart 2 -> no more restarts
        restart_pids = []
        
        for i in range(3):
            status = supervisor.get_status()
            if status["limit_test"]["pid"]:
                pid = status["limit_test"]["pid"]
                restart_pids.append(pid)
                os.kill(pid, signal.SIGKILL)
                
                if i < 2:
                    # Wait for restart (should happen for first 2 kills)
                    await asyncio.sleep(8)  # Give plenty of time for restart
                else:
                    # After 3rd kill, wait for health check to detect and refuse restart
                    await asyncio.sleep(3)  # Health check interval + processing time
        
        # Verify we had exactly 3 different PIDs (original + 2 restarts)
        assert len(set(restart_pids)) == 3, f"Expected 3 unique PIDs, got {restart_pids}"
        
        # Check final status
        status = supervisor.get_status()
        
        # Agent should be stopped after exceeding restart limit
        assert status["limit_test"]["status"] == "stopped"
        
    finally:
        await supervisor.stop_all()
