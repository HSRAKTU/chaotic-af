#!/usr/bin/env python3
"""
Dynamic Agent Connections Demo

This demo shows the new dynamic connection capabilities:
- Use ANY agent names (not restricted to researcher/writer/coordinator)
- Use ANY ports
- Create custom connection topologies
- Add connections at runtime
"""

import asyncio
import sys
sys.path.append('..')

from agent_framework import AgentSupervisor, AgentConfig


async def main():
    # Clean up any previous runs
    import subprocess
    subprocess.run("pkill -f agent_framework.network.agent_runner || true", shell=True)
    await asyncio.sleep(1)
    
    print("\n🚀 Dynamic Agent Framework Demo\n")
    
    # Create agents with custom names and ports
    weather_bot = AgentConfig(
        name="weather_bot",
        port=5001,
        llm_provider="google",
        llm_model="gemini-1.5-pro",
        role_prompt="You are a weather expert. Provide weather information and forecasts.",
        external_mcp_servers=[],
        log_level="INFO"
    )
    
    news_agent = AgentConfig(
        name="news_agent",
        port=5002,
        llm_provider="google",
        llm_model="gemini-1.5-pro",
        role_prompt="You are a news analyst. Provide current news and analysis.",
        external_mcp_servers=[],
        log_level="INFO"
    )
    
    coordinator = AgentConfig(
        name="coordinator",
        port=5003,
        llm_provider="google",
        llm_model="gemini-1.5-pro",
        role_prompt="You coordinate between other agents to provide comprehensive answers.",
        external_mcp_servers=[],
        log_level="INFO"
    )
    
    # Create supervisor and add agents
    supervisor = AgentSupervisor()
    supervisor.add_agent(weather_bot)
    supervisor.add_agent(news_agent)
    supervisor.add_agent(coordinator)
    
    # Start all agents
    print("Starting agents...")
    await supervisor.start_all()
    await asyncio.sleep(3)
    
    # Create custom connections
    print("\n🔗 Creating connections...")
    
    # Coordinator can talk to both weather and news
    await supervisor.connect("coordinator", "weather_bot")
    await supervisor.connect("coordinator", "news_agent")
    
    # Weather and news can respond back to coordinator
    await supervisor.connect("weather_bot", "coordinator")
    await supervisor.connect("news_agent", "coordinator")
    
    print("\n✅ Agents connected!")
    print("\nTopology:")
    print("  coordinator ←→ weather_bot")
    print("  coordinator ←→ news_agent")
    
    # Now you can interact with the agents via their MCP endpoints
    print("\nAgents are running and connected!")
    print("You can now:")
    print("- Connect to coordinator at http://localhost:5003/mcp")
    print("- Ask it to check weather or news")
    print("- It will coordinate with the other agents")
    
    # Keep running for demonstration
    print("\nPress Ctrl+C to stop...")
    try:
        await asyncio.Event().wait()
    except KeyboardInterrupt:
        pass
    
    print("\nShutting down...")
    await supervisor.stop_all()


if __name__ == "__main__":
    asyncio.run(main())
