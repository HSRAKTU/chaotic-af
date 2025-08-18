#!/usr/bin/env python3
"""
Military-Style Three Agent Discussion Demo
- Alpha, Bravo, Charlie agents
- Fully bidirectional connections (each agent can talk to both others)
- Live interaction logging
"""

import asyncio
import sys
import os
from pathlib import Path

sys.path.append('.')

from agent_framework import AgentSupervisor, AgentConfig
from agent_framework.mcp.client import AgentMCPClient
from agent_framework.core.logging import AgentLogger
from agent_framework.core.events import EventStream


async def run_military_demo():
    """Run the military agent discussion demo"""
    # Clear logs
    log_dir = Path("logs")
    if log_dir.exists():
        for f in log_dir.iterdir():
            if f.is_file():
                f.unlink()
    
    print("\n🚀 Starting Military Agent System (Alpha, Bravo, Charlie)...\n")
    
    # Create supervisor
    supervisor = AgentSupervisor()
    
    try:
        # Define three military agents with specific expertise
        alpha = AgentConfig(
            name="alpha",
            port=7001,
            llm_provider="google",
            llm_model="gemini-1.5-pro",
            role_prompt="""You are Agent Alpha, a strategic military commander.
You specialize in high-level strategy and coordination.
You can communicate with both Bravo and Charlie using the contact_agent tool.
Keep responses concise but strategic.""",
            log_level="INFO"
        )
        
        bravo = AgentConfig(
            name="bravo",
            port=7002,
            llm_provider="google",
            llm_model="gemini-1.5-pro",
            role_prompt="""You are Agent Bravo, a tactical operations specialist.
You focus on ground-level tactics and immediate actions.
You can communicate with both Alpha and Charlie using the contact_agent tool.
Keep responses tactical and action-oriented.""",
            log_level="INFO"
        )
        
        charlie = AgentConfig(
            name="charlie",
            port=7003,
            llm_provider="google",
            llm_model="gemini-1.5-pro",
            role_prompt="""You are Agent Charlie, an intelligence analyst.
You provide data, analysis, and situational awareness.
You can communicate with both Alpha and Bravo using the contact_agent tool.
Keep responses analytical with key intel points.""",
            log_level="INFO"
        )
        
        # Add agents
        supervisor.add_agent(alpha)
        supervisor.add_agent(bravo)
        supervisor.add_agent(charlie)
        
        # Start all agents
        print("🔄 Starting military agents...")
        await supervisor.start_all()
        await asyncio.sleep(3)
        print("✅ All agents operational\n")
        
        # Create BIDIRECTIONAL connections - each agent can talk to both others
        print("🔗 Establishing secure communications...")
        
        # Alpha connections
        await supervisor.connect("alpha", "bravo")
        await supervisor.connect("alpha", "charlie")
        
        # Bravo connections
        await supervisor.connect("bravo", "alpha")
        await supervisor.connect("bravo", "charlie")
        
        # Charlie connections
        await supervisor.connect("charlie", "alpha")
        await supervisor.connect("charlie", "bravo")
        
        await asyncio.sleep(2)
        print("✅ All agents have bidirectional comms established")
        print("   Alpha ↔️ Bravo")
        print("   Alpha ↔️ Charlie")
        print("   Bravo ↔️ Charlie")
        print()
        
        # Test communication
        print("💬 Initiating mission briefing...\n")
        print("=" * 80)
        print("LIVE MILITARY AGENT DISCUSSION:")
        print("=" * 80 + "\n")
        
        # Create a client
        logger = AgentLogger("command")
        event_stream = EventStream(agent_id="command")
        
        client = AgentMCPClient(
            agent_id="command",
            event_stream=event_stream,
            logger=logger
        )
        
        await client.add_connection("alpha", f"http://localhost:{alpha.port}/mcp")
        
        # Start a strategic discussion
        print("🎖️ COMMAND → ALPHA: We need to plan a reconnaissance mission in the northern sector. Coordinate with Bravo for tactical approach and Charlie for intel assessment. What's your strategic recommendation?\n")
        
        result = await client.call_tool(
            server_name="alpha",
            tool_name="chat_with_user",
            arguments={
                "message": "We need to plan a reconnaissance mission in the northern sector. Coordinate with Bravo for tactical approach and Charlie for intel assessment. What's your strategic recommendation?"
            }
        )
        
        print("\n" + "=" * 80)
        print(f"ALPHA'S STRATEGIC RESPONSE: {result.data.get('response', 'No response')}")
        print("=" * 80)
        
        # Let's give them time to complete their discussion
        await asyncio.sleep(10)
        
        # Ask for a follow-up from Bravo
        print("\n🎖️ COMMAND → BRAVO: What tactical elements did you discuss with Alpha and Charlie?\n")
        
        await client.add_connection("bravo", f"http://localhost:{bravo.port}/mcp")
        
        result2 = await client.call_tool(
            server_name="bravo",
            tool_name="chat_with_user",
            arguments={
                "message": "What tactical elements did you discuss with Alpha and Charlie for the reconnaissance mission?"
            }
        )
        
        print("\n" + "=" * 80)
        print(f"BRAVO'S TACTICAL REPORT: {result2.data.get('response', 'No response')}")
        print("=" * 80)
        
        await client.close_all()
        
        print("\n✅ Mission briefing complete!")
        
    finally:
        # Always clean up
        await supervisor.stop_all()


async def main():
    """Main function with timeout wrapper"""
    try:
        # Run demo with 120 second timeout
        await asyncio.wait_for(run_military_demo(), timeout=120.0)
    except asyncio.TimeoutError:
        print("\n⏰ Demo timeout after 120 seconds - shutting down...")
        # Force cleanup if needed
        import subprocess
        subprocess.run("pkill -f agent_framework.network.agent_runner", shell=True, capture_output=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nShutting down...")
