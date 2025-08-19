"""Test metrics collection functionality."""

import asyncio
import pytest
import json
from agent_framework import AgentSupervisor, AgentConfig
from agent_framework.core.metrics import MetricsCollector, AgentMetrics


@pytest.mark.asyncio
async def test_metrics_basic():
    """Test basic metrics collection functionality."""
    
    # Create metrics collector
    collector = MetricsCollector()
    metrics = AgentMetrics(collector)
    
    # Test counter metrics
    metrics.inc_messages_sent("alice", "bob")
    metrics.inc_messages_sent("alice", "bob")
    metrics.inc_messages_received("alice", "bob")
    
    # Test gauge metrics
    metrics.set_agent_up("alice", True)
    metrics.set_active_connections("alice", 3)
    
    # Test histogram metrics
    metrics.observe_message_duration("alice", 0.150)
    metrics.observe_message_duration("alice", 0.200)
    metrics.observe_message_duration("alice", 0.050)
    
    # Get JSON metrics
    json_metrics = collector.get_metrics_json()
    
    # Verify counters
    assert json_metrics["counters"]["agent_messages_sent_total{agent=\"alice\",peer=\"bob\"}"]["value"] == 2.0
    assert json_metrics["counters"]["agent_messages_received_total{agent=\"alice\",peer=\"bob\"}"]["value"] == 1.0
    
    # Verify gauges
    assert json_metrics["gauges"]["agent_up{agent=\"alice\"}"]["value"] == 1.0
    assert json_metrics["gauges"]["agent_connections_active{agent=\"alice\"}"]["value"] == 3.0
    
    # Verify histograms
    hist = json_metrics["histograms"]["agent_message_duration_seconds{agent=\"alice\"}"]
    assert hist["count"] == 3
    assert hist["min"] == 0.050
    assert hist["max"] == 0.200
    assert 0.1 < hist["avg"] < 0.2


@pytest.mark.asyncio
async def test_metrics_prometheus_format():
    """Test Prometheus format export."""
    
    # Create metrics collector
    collector = MetricsCollector()
    metrics = AgentMetrics(collector)
    
    # Add some metrics
    metrics.set_agent_up("test_agent", True)
    metrics.inc_messages_sent("test_agent", "peer1")
    metrics.observe_llm_duration("test_agent", "google", 1.5)
    
    # Get Prometheus format
    prom_text = collector.get_metrics_prometheus()
    
    # Verify format
    assert "# HELP agent_up Whether the agent is up" in prom_text
    assert "# TYPE agent_up gauge" in prom_text
    assert 'agent_up{agent="test_agent"} 1.0' in prom_text
    
    assert "# HELP agent_messages_sent_total Total messages sent" in prom_text
    assert "# TYPE agent_messages_sent_total counter" in prom_text
    
    assert "# HELP agent_llm_request_duration_seconds Time for LLM API calls" in prom_text
    assert "# TYPE agent_llm_request_duration_seconds histogram" in prom_text
    # Check histogram bucket exists (format might vary slightly)
    assert 'agent_llm_request_duration_seconds_bucket' in prom_text
    assert 'le="2.5"' in prom_text
    assert 'agent="test_agent"' in prom_text
    assert 'provider="google"' in prom_text


@pytest.mark.asyncio
async def test_metrics_via_socket():
    """Test metrics collection via agent socket."""
    
    # Create supervisor with socket mode
    supervisor = AgentSupervisor()
    
    # Create test agent
    test_agent = AgentConfig(
        name="metrics_test",
        llm_provider="google",
        llm_model="gemini-1.5-pro",
        role_prompt="Test agent for metrics",
        port=8801
    )
    
    supervisor.add_agent(test_agent)
    
    try:
        # Start agent
        await supervisor.start_all(monitor=False)
        await asyncio.sleep(3)
        
        # Query metrics via socket
        socket_path = "/tmp/chaotic-af/agent-metrics_test.sock"
        reader, writer = await asyncio.open_unix_connection(socket_path)
        
        # Request JSON metrics
        cmd = {"cmd": "metrics", "format": "json"}
        writer.write(json.dumps(cmd).encode() + b'\n')
        await writer.drain()
        
        response = await reader.readline()
        result = json.loads(response.decode())
        
        # Verify we got metrics
        assert "metrics" in result
        assert "counters" in result["metrics"]
        assert "gauges" in result["metrics"]
        assert "histograms" in result["metrics"]
        
        writer.close()
        await writer.wait_closed()
        
        # Request Prometheus metrics
        reader, writer = await asyncio.open_unix_connection(socket_path)
        cmd = {"cmd": "metrics", "format": "prometheus"}
        writer.write(json.dumps(cmd).encode() + b'\n')
        await writer.drain()
        
        response = await reader.readline()
        result = json.loads(response.decode())
        
        # Verify Prometheus format
        assert "metrics" in result
        assert "# HELP" in result["metrics"]
        assert "# TYPE" in result["metrics"]
        
        writer.close()
        await writer.wait_closed()
        
    finally:
        await supervisor.stop_all()


@pytest.mark.asyncio
async def test_supervisor_metrics():
    """Test supervisor-level metrics aggregation."""
    
    # Create supervisor
    supervisor = AgentSupervisor()
    
    # Create multiple agents
    agents = [
        AgentConfig(
            name="agent1",
            llm_provider="google",
            llm_model="gemini-1.5-pro",
            role_prompt="Test agent 1",
            port=8811
        ),
        AgentConfig(
            name="agent2",
            llm_provider="google",
            llm_model="gemini-1.5-pro",
            role_prompt="Test agent 2",
            port=8812
        )
    ]
    
    for agent in agents:
        supervisor.add_agent(agent)
    
    try:
        # Start all agents
        await supervisor.start_all(monitor=False)
        await asyncio.sleep(3)
        
        # Get supervisor metrics
        supervisor_metrics = supervisor.metrics_collector.get_metrics_json()
        
        # Verify agent up metrics
        assert supervisor_metrics["gauges"]["agent_up{agent=\"agent1\"}"]["value"] == 1.0
        assert supervisor_metrics["gauges"]["agent_up{agent=\"agent2\"}"]["value"] == 1.0
        
        # Stop one agent
        await supervisor.stop_agent("agent1")
        await asyncio.sleep(1)
        
        # Verify updated metrics
        supervisor_metrics = supervisor.metrics_collector.get_metrics_json()
        assert supervisor_metrics["gauges"]["agent_up{agent=\"agent1\"}"]["value"] == 0.0
        assert supervisor_metrics["gauges"]["agent_up{agent=\"agent2\"}"]["value"] == 1.0
        
    finally:
        await supervisor.stop_all()
