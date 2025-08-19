"""Quick test to verify CPU fix works."""

import asyncio
import psutil
import time
import pytest
from agent_framework import AgentSupervisor, AgentConfig


@pytest.mark.asyncio
async def test_cpu_usage():
    """Test that socket mode fixes CPU usage."""
    print("Testing CPU usage fix...")
    
    # Create supervisor with socket mode
    supervisor = AgentSupervisor(use_sockets=True)
    
    # Create test agent
    alice = AgentConfig(
        name="alice",
        llm_provider="google",
        llm_model="gemini-1.5-pro",
        role_prompt="Test agent",
        port=8201
    )
    
    supervisor.add_agent(alice)
    
    # Start agent
    print("Starting agent in socket mode...")
    await supervisor.start_agent("alice", monitor_output=False)
    
    # Wait for startup
    await asyncio.sleep(3)
    
    # Check CPU
    agent_proc = supervisor.agents["alice"]
    if agent_proc.pid:
        proc = psutil.Process(agent_proc.pid)
        
        # Sample CPU over 3 seconds
        print("Measuring CPU usage...")
        cpu = proc.cpu_percent(interval=3.0)
        
        print(f"CPU Usage: {cpu}%")
        
        if cpu < 5.0:
            print("✅ SUCCESS: CPU usage is low!")
        else:
            print(f"❌ FAILED: CPU usage is {cpu}%")
    
    # Cleanup
    await supervisor.stop_all()


if __name__ == "__main__":
    asyncio.run(test_cpu_usage())
