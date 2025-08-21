"""Demo: Three agents discussing autonomously.

This example shows:
1. Three agents with different expertise
2. They discuss a topic by their own decisions
3. Works with both CLI and library approaches
"""

import asyncio
from agent_framework import AgentSupervisor, AgentConfig, AgentMCPClient, EventStream
from agent_framework.core.logging import AgentLogger


async def main():
    print("=== Three Bot Discussion Demo ===\n")
    
    # Create supervisor
    supervisor = AgentSupervisor()
    
    # Define three agents with complementary expertise
    alice = AgentConfig(
        name="alice",
        llm_provider="google",
        llm_model="gemini-1.5-pro",
        role_prompt="""You are Alice, a creative writer and philosopher. 
        You love discussing abstract concepts and exploring ideas.
        When you hear an interesting topic, actively engage by asking thought-provoking questions
        and sharing your creative perspectives. Always address other agents by name.""",
        port=8401
    )
    
    bob = AgentConfig(
        name="bob",
        llm_provider="google",
        llm_model="gemini-1.5-pro", 
        role_prompt="""You are Bob, a practical engineer and scientist.
        You approach topics with logic and data. When discussing ideas,
        you provide technical insights and real-world applications.
        Challenge abstract ideas with practical considerations. Always address other agents by name.""",
        port=8402
    )
    
    charlie = AgentConfig(
        name="charlie",
        llm_provider="google",
        llm_model="gemini-1.5-pro",
        role_prompt="""You are Charlie, a historian and cultural expert.
        You provide historical context and cultural perspectives to any discussion.
        Bridge the gap between creative and practical viewpoints with examples from history.
        Keep discussions flowing by asking follow-up questions. Always address other agents by name.""",
        port=8403
    )
    
    # Add agents
    supervisor.add_agent(alice)
    supervisor.add_agent(bob)
    supervisor.add_agent(charlie)
    
    try:
        print("1. Starting agents...")
        await supervisor.start_all(monitor=False)
        await asyncio.sleep(3)
        print("✓ All agents started\n")
        
        print("2. Creating discussion network...")
        # Connect in a triangle - everyone can talk to everyone
        await supervisor.connect("alice", "bob", bidirectional=True)
        await supervisor.connect("bob", "charlie", bidirectional=True)
        await supervisor.connect("charlie", "alice", bidirectional=True)
        print("✓ Discussion network created: Alice ↔ Bob ↔ Charlie ↔ Alice\n")
        
        print("3. Starting discussion about 'The Future of AI'...\n")
        print("-" * 60)
        
        # Create a client to kick off the discussion
        client = AgentMCPClient(
            agent_id="moderator",
            event_stream=EventStream(agent_id="moderator"),
            logger=AgentLogger("moderator", "INFO")
        )
        
        # Connect to Alice to start the discussion
        await client.add_connection("alice", "http://localhost:8401/mcp")
        
        # Start the discussion
        response = await client.call_tool(
            server_name="alice",
            tool_name="chat_with_user",
            arguments={
                "message": """Alice, I'd like you to start a discussion with Bob and Charlie about 
                'The Future of AI and Human Creativity'. Share your thoughts and ask them for their 
                perspectives. Let the conversation flow naturally for a few exchanges."""
            }
        )
        
        print(f"Alice: {response.data['response']}\n")
        
        # Let the agents discuss autonomously for a bit
        print("(Agents continue discussing autonomously...)\n")
        await asyncio.sleep(10)
        
        # Check in with Bob
        await client.add_connection("bob", "http://localhost:8402/mcp")
        response = await client.call_tool(
            server_name="bob",
            tool_name="chat_with_user",
            arguments={
                "message": "Bob, what are your thoughts on the discussion so far?"
            }
        )
        print(f"\nModerator check-in - Bob: {response.data['response']}\n")
        
        # Check in with Charlie
        await client.add_connection("charlie", "http://localhost:8403/mcp")
        response = await client.call_tool(
            server_name="charlie",
            tool_name="chat_with_user",
            arguments={
                "message": "Charlie, any historical parallels you'd like to share?"
            }
        )
        print(f"\nModerator check-in - Charlie: {response.data['response']}\n")
        
        print("-" * 60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        print("\n4. Shutting down discussion...")
        if 'client' in locals():
            await client.close_all()
        await supervisor.stop_all()
        print("✓ All agents stopped")


if __name__ == "__main__":
    print("Starting Three Bot Discussion Demo...")
    print("Watch as Alice (creative), Bob (practical), and Charlie (historical) discuss AI!\n")
    
    asyncio.run(main())
