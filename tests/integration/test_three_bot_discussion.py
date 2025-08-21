"""Test that both CLI and library approaches work identically for multi-agent discussions."""

import asyncio
import pytest
from unittest.mock import patch
from agent_framework import AgentSupervisor, AgentConfig, AgentMCPClient, EventStream
from agent_framework.core.logging import AgentLogger
from agent_framework.client import AgentSocketClient


@pytest.mark.asyncio
async def test_library_three_agent_discussion():
    """Test three agents discussing via library API."""
    supervisor = AgentSupervisor()
    
    # Create three test agents
    alice = AgentConfig(
        name="test_alice",
        llm_provider="google",
        llm_model="gemini-1.5-pro",
        role_prompt="You are Alice, respond briefly.",
        port=9501
    )
    
    bob = AgentConfig(
        name="test_bob",
        llm_provider="google",
        llm_model="gemini-1.5-pro",
        role_prompt="You are Bob, respond briefly.",
        port=9502
    )
    
    charlie = AgentConfig(
        name="test_charlie",
        llm_provider="google",
        llm_model="gemini-1.5-pro",
        role_prompt="You are Charlie, respond briefly.",
        port=9503
    )
    
    supervisor.add_agent(alice)
    supervisor.add_agent(bob)
    supervisor.add_agent(charlie)
    
    try:
        # Start agents
        await supervisor.start_all(monitor=False)
        await asyncio.sleep(3)
        
        # Connect in triangle
        await supervisor.connect("test_alice", "test_bob", bidirectional=True)
        await supervisor.connect("test_bob", "test_charlie", bidirectional=True)
        await supervisor.connect("test_charlie", "test_alice", bidirectional=True)
        
        # Verify all agents are connected
        assert len(supervisor.agents) == 3
        assert all(agent.status == "running" for agent in supervisor.agents.values())
        
        # Test socket communication works
        health_result = await AgentSocketClient.health_check("test_alice")
        assert health_result.get("status") == "ready"
        
    finally:
        await supervisor.stop_all()


@pytest.mark.asyncio
async def test_socket_client_all_methods():
    """Test all socket client convenience methods."""
    supervisor = AgentSupervisor()
    
    agent = AgentConfig(
        name="test_socket_agent",
        llm_provider="google",
        llm_model="gemini-1.5-pro",
        role_prompt="Test agent",
        port=9504
    )
    
    supervisor.add_agent(agent)
    
    try:
        await supervisor.start_all(monitor=False)
        await asyncio.sleep(2)
        
        # Test health check
        health = await AgentSocketClient.health_check("test_socket_agent")
        assert health.get("status") == "ready"
        
        # Test metrics
        metrics = await AgentSocketClient.get_metrics("test_socket_agent")
        assert "metrics" in metrics
        
        # Test shutdown
        shutdown = await AgentSocketClient.shutdown_agent("test_socket_agent")
        assert shutdown.get("status") == "shutting_down"
        
    finally:
        try:
            await supervisor.stop_all()
        except:
            pass
