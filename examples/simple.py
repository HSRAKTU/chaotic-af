#!/usr/bin/env python3
"""
Clean Multi-Agent Demo with Minimal Logging
"""

import asyncio
import sys
import os
import logging
from pathlib import Path

# Suppress verbose logging
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("uvicorn").setLevel(logging.WARNING)
logging.getLogger("fastapi").setLevel(logging.WARNING)

sys.path.append('.')

from agent_framework import AgentSupervisor, AgentConfig
from agent_framework.mcp.client import AgentMCPClient


async def run_demo_with_timeout():
    """Run the demo with a 120 second timeout"""
    # Clear logs
    log_dir = Path("logs")
    if log_dir.exists():
        for f in log_dir.iterdir():
            if f.is_file():
                f.unlink()
    
    print("\n🚀 Starting Multi-Agent System...\n")
    
    # Create supervisor with ERROR level logging to minimize output
    supervisor = AgentSupervisor()
    
    try:
        # Define three agents
        alice = AgentConfig(
            name="alice",
            port=6001,
            llm_provider="google",
            llm_model="gemini-1.5-pro",
            role_prompt="You are Alice, a helpful assistant.",
            log_level="ERROR"  # Minimal logging
        )
        
        bob = AgentConfig(
            name="bob",
            port=6002,
            llm_provider="google",
            llm_model="gemini-1.5-pro",
            role_prompt="You are Bob, an expert in geography and history.",
            log_level="ERROR"  # Minimal logging
        )
        
        charlie = AgentConfig(
            name="charlie",
            port=6003,
            llm_provider="google",
            llm_model="gemini-1.5-pro",
            role_prompt="You are Charlie, a creative storyteller.",
            log_level="ERROR"  # Minimal logging
        )
        
        # Add agents
        supervisor.add_agent(alice)
        supervisor.add_agent(bob)
        supervisor.add_agent(charlie)
        
        # Redirect supervisor logs to minimize output
        supervisor.logger.logger.setLevel(logging.ERROR)
        
        # Start all agents
        await supervisor.start_all()
        await asyncio.sleep(3)
        print("✅ All agents are online")
        
        # Create connections
        await supervisor.connect("alice", "bob")
        await supervisor.connect("bob", "charlie")
        await supervisor.connect("charlie", "alice")
        await asyncio.sleep(2)
        print("✅ Connections established: alice→bob→charlie→alice")
        
        # Test communication
        print("\n💬 Starting conversation...\n")
        
        # Create a client with a silent logger and event stream
        from agent_framework.core.logging import AgentLogger
        from agent_framework.core.events import EventStream
        
        silent_logger = AgentLogger("user")
        silent_logger.logger.setLevel(logging.CRITICAL)  # Suppress all logs
        
        # Create minimal event stream
        event_stream = EventStream(agent_id="user")
        
        client = AgentMCPClient(
            agent_id="user",
            event_stream=event_stream,
            logger=silent_logger
        )
        
        await client.add_connection("alice", f"http://localhost:{alice.port}/mcp")
        
        # Ask Alice to coordinate with Bob
        result = await client.call_tool(
            server_name="alice",
            tool_name="chat_with_user",
            arguments={
                "message": "Please ask Bob what the capital of France is."
            }
        )
        
        print(f"Alice: {result.data.get('response', 'No response')}")
        
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
    # Suppress asyncio debug logs
    os.environ["PYTHONASYNCIODEBUG"] = "0"
    
    # Disable asyncio debug mode
    loop = asyncio.new_event_loop()
    loop.set_debug(False)
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(main())
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        loop.close()