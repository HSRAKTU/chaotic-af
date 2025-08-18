"""Example: Using Chaotic AF as a Python library.

This example shows how to:
1. Create agents programmatically
2. Start them with socket mode (no CPU waste)
3. Connect agents dynamically
4. Send messages between agents
5. Clean shutdown
"""

import asyncio
from agent_framework import AgentSupervisor, AgentConfig, AgentMCPClient, EventStream


async def main():
    print("=== Chaotic AF Library Example ===\n")
    
    # Create supervisor (socket mode is now default)
    supervisor = AgentSupervisor()
    client = None
    
    # Define agents
    alice = AgentConfig(
        name="alice",
        llm_provider="google",
        llm_model="gemini-1.5-pro",
        role_prompt="You are Alice, a helpful assistant. When asked, you can contact other agents for help.",
        port=8301
    )
    
    bob = AgentConfig(
        name="bob",
        llm_provider="google", 
        llm_model="gemini-1.5-pro",
        role_prompt="You are Bob, an expert in geography and world capitals.",
        port=8302
    )
    
    # Add agents to supervisor
    supervisor.add_agent(alice)
    supervisor.add_agent(bob)
    
    try:
        print("1. Starting agents...")
        await supervisor.start_all(monitor=False)
        
        # Wait for agents to be ready
        await asyncio.sleep(3)
        print("✓ Agents started (CPU usage < 1%)\n")
        
        # Connect agents
        print("2. Connecting agents...")
        await supervisor.connect("alice", "bob", bidirectional=True)
        print("✓ Alice ↔ Bob connected\n")
        
        # Create a client to interact with Alice
        print("3. Sending message to Alice...")
        from agent_framework.core.logging import AgentLogger
        
        client = AgentMCPClient(
            agent_id="user",
            event_stream=EventStream(agent_id="user"),
            logger=AgentLogger("user", "INFO")
        )
        
        # Add connection to Alice
        await client.add_connection("alice", "http://localhost:8301/mcp")
        
        # Send a message that requires Alice to contact Bob
        response = await client.call_tool(
            server_name="alice",
            tool_name="chat_with_user",
            arguments={
                "message": "Hi Alice! Can you ask Bob what the capital of France is?"
            }
        )
        
        print(f"Alice's response: {response.data['response']}\n")
        
        # Direct message to verify Bob knows the answer
        await client.add_connection("bob", "http://localhost:8302/mcp")
        
        response = await client.call_tool(
            server_name="bob",
            tool_name="chat_with_user",
            arguments={
                "message": "What is the capital of France?"
            }
        )
        
        print(f"Bob's direct response: {response.data['response']}\n")
        
        # Check agent status
        print("4. Agent Status:")
        status = supervisor.get_status()
        for agent_name, info in status.items():
            print(f"   {agent_name}: {info['status']} on port {info['port']}")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Always clean up
        print("\n5. Shutting down...")
        if client:
            try:
                await client.close_all()
            except:
                pass
        
        try:
            await supervisor.stop_all()
        except:
            pass
            
        print("✓ Cleanup complete")


if __name__ == "__main__":
    print("Starting Chaotic AF library example...")
    print("This demonstrates programmatic agent management.\n")
    
    asyncio.run(main())
