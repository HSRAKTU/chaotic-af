#!/usr/bin/env python3
"""
Live Multi-Agent Demo - Shows all tool calls and responses in real-time
"""

import asyncio
import sys
import os
import logging
from pathlib import Path

sys.path.append('.')

from agent_framework import AgentSupervisor, AgentConfig
from agent_framework.mcp.client import AgentMCPClient
from agent_framework.core.logging import AgentLogger
from agent_framework.core.events import EventStream


async def run_demo_with_timeout():
    """Run the demo with a 120 second timeout"""
    # Clear logs
    log_dir = Path("logs")
    if log_dir.exists():
        for f in log_dir.iterdir():
            if f.is_file():
                f.unlink()
    
    print("\n🚀 Starting Multi-Agent System with Live Logging...\n")
    
    # Create supervisor
    supervisor = AgentSupervisor()
    
    try:
        # Define three agents with INFO logging to see tool calls
        alice = AgentConfig(
            name="alice",
            port=6001,
            llm_provider="google",
            llm_model="gemini-1.5-pro",
            role_prompt="You are Alice, a helpful assistant.",
            log_level="INFO"  # Show all agent activity
        )
        
        bob = AgentConfig(
            name="bob",
            port=6002,
            llm_provider="google",
            llm_model="gemini-1.5-pro",
            role_prompt="You are Bob, an expert in geography and history.",
            log_level="INFO"  # Show all agent activity
        )
        
        charlie = AgentConfig(
            name="charlie",
            port=6003,
            llm_provider="google",
            llm_model="gemini-1.5-pro",
            role_prompt="You are Charlie, a creative storyteller.",
            log_level="INFO"  # Show all agent activity
        )
        
        # Add agents
        supervisor.add_agent(alice)
        supervisor.add_agent(bob)
        supervisor.add_agent(charlie)
        
        # Start all agents
        print("🔄 Starting agents...")
        await supervisor.start_all()
        await asyncio.sleep(3)
        print("✅ All agents are online\n")
        
        # Create connections
        print("🔗 Establishing connections...")
        await supervisor.connect("alice", "bob")
        await supervisor.connect("bob", "charlie")
        await supervisor.connect("charlie", "alice")
        await asyncio.sleep(2)
        print("✅ Connections established: alice→bob→charlie→alice\n")
        
        # Test communication
        print("💬 Starting conversation...\n")
        print("=" * 80)
        print("LIVE AGENT INTERACTIONS:")
        print("=" * 80 + "\n")
        
        # Create a client with normal logging
        logger = AgentLogger("user")
        event_stream = EventStream(agent_id="user")
        
        client = AgentMCPClient(
            agent_id="user",
            event_stream=event_stream,
            logger=logger
        )
        
        await client.add_connection("alice", f"http://localhost:{alice.port}/mcp")
        
        # Ask Alice to coordinate with Bob
        print("👤 USER → ALICE: Please ask Bob what the capital of France is.\n")
        
        result = await client.call_tool(
            server_name="alice",
            tool_name="chat_with_user",
            arguments={
                "message": "Please ask Bob what the capital of France is."
            }
        )
        
        print("\n" + "=" * 80)
        print(f"FINAL RESPONSE FROM ALICE: {result.data.get('response', 'No response')}")
        print("=" * 80)
        
        await client.close_all()
        
        print("\n✅ Demo complete!")
        
    finally:
        # Always clean up
        await supervisor.stop_all()


async def main():
    """Main function with timeout wrapper"""
    try:
        # Run demo with 120 second timeout
        await asyncio.wait_for(run_demo_with_timeout(), timeout=120.0)
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
