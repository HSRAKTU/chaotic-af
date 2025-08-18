#!/bin/bash

# Chaotic AF CLI Usage Example
# This demonstrates using agentctl to manage agents

echo "=== Chaotic AF CLI Example ==="
echo
echo "This example shows how to:"
echo "1. Start agents using YAML configs"
echo "2. Connect agents dynamically"
echo "3. Check agent status"
echo "4. Clean shutdown"
echo

# Clean up any existing agents
echo "Cleaning up existing agents..."
agentctl stop --all 2>/dev/null || true
pkill -f agent_framework.network.agent_runner 2>/dev/null || true
sleep 1

# Start agents
echo
echo "1. Starting agents..."
echo "   $ agentctl start alice.yaml bob.yaml charlie.yaml"
agentctl start alice.yaml bob.yaml charlie.yaml

# Wait for agents to be ready
sleep 3

# Check status
echo
echo "2. Checking agent status..."
echo "   $ agentctl status"
agentctl status

# Connect agents
echo
echo "3. Connecting agents..."
echo "   $ agentctl connect alice bob -b"
agentctl connect alice bob -b

echo "   $ agentctl connect alice charlie -b"
agentctl connect alice charlie -b

# Show how to interact with agents
echo
echo "4. Agents are now ready for interaction!"
echo
echo "You can now:"
echo "- Send messages to Alice who will coordinate with Bob and Charlie"
echo "- Use the Python client to interact with agents"
echo "- Monitor agent logs in the logs/ directory"
echo

# Keep running for a bit
echo "Agents will run for 30 seconds, then shutdown..."
sleep 30

# Clean shutdown
echo
echo "5. Shutting down agents..."
echo "   $ agentctl stop --all"
agentctl stop --all

echo
echo "Demo complete!"
