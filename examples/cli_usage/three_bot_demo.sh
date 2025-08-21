#!/bin/bash
# Demo: Three agents discussing via CLI

echo "=== Three Bot Discussion Demo (CLI) ==="
echo ""

# Start agents
echo "1. Starting agents..."
agentctl start alice_philosopher.yaml &
agentctl start bob_engineer.yaml &
agentctl start charlie_historian.yaml &

# Wait for agents to start
sleep 5

echo "✓ All agents started"
echo ""

# Check status
echo "2. Agent status:"
agentctl status
echo ""

# Create discussion network
echo "3. Creating discussion network..."
agentctl connect alice bob
agentctl connect bob charlie  
agentctl connect charlie alice
echo "✓ Discussion network created: Alice ↔ Bob ↔ Charlie ↔ Alice"
echo ""

echo "4. Starting discussion about 'The Future of AI'..."
echo "-----------------------------------------------------------"

# Kick off the discussion
agentctl chat alice "Alice, I'd like you to start a discussion with Bob and Charlie about 'The Future of AI and Human Creativity'. Share your thoughts and ask them for their perspectives."

echo ""
echo "(Agents continue discussing autonomously...)"
echo ""

# Let them discuss
sleep 10

# Check in with each agent
echo ""
echo "Moderator check-in with Bob:"
agentctl chat bob "Bob, what are your thoughts on the discussion so far?"

echo ""
echo "Moderator check-in with Charlie:"
agentctl chat charlie "Charlie, any historical parallels you'd like to share?"

echo "-----------------------------------------------------------"
echo ""

# Cleanup
echo "5. Stopping agents..."
agentctl stop alice
agentctl stop bob
agentctl stop charlie

echo "✓ Demo complete"
