# Multi-Agent UI Monitor

## Quick Start

### 1. Install UI Dependencies
```bash
pip install -r requirements-ui.txt
```

### 2. Start UI Server
```bash
python ui_server.py
```

### 3. Open Dashboard
Open http://localhost:8080 in your browser

## Features

### Network Topology
- Visual agent nodes positioned in circle layout
- Connection wires showing bidirectional relationships
- Color-coded status: Green (running), Orange (starting), Red (failed)

### Live Event Stream
- Real-time monitoring of ALL agent interactions
- Shows events from ALL agents simultaneously
- Same arrow logic as CLI: → (outgoing), ← (incoming)
- Color-coded events: Green (outgoing), Blue (incoming), Orange (thinking)

### Chat Interface
- Dropdown to select any running agent
- Text area for messages
- Send button or Enter key to send
- Verbose mode checkbox
- "Trigger Chaos Test" button for multi-agent propagation testing

## Chaos Mode Testing

### Enable Chaos Mode
Use chaos-enabled configs:
```bash
python -m agent_framework.cli.commands start *_chaos.yaml
python -m agent_framework.cli.commands connect customer_service tech_support -b
python -m agent_framework.cli.commands connect customer_service billing -b  
python -m agent_framework.cli.commands connect customer_service shipping -b
python -m agent_framework.cli.commands connect tech_support billing -b
python -m agent_framework.cli.commands connect tech_support shipping -b
python -m agent_framework.cli.commands connect billing shipping -b
```

### Test Multi-Agent Chains
In the UI:
1. Select an agent from dropdown
2. Type: "PROPAGATION DRILL: Pass this message through ALL agents in sequence"
3. Click "Send Message" or "Trigger Chaos Test" 
4. Watch the network topology and event stream show complete multi-agent discussion chains

### What You'll See
- Complete visibility of agent-to-agent coordination
- Multi-hop message propagation
- Internal agent discussions before final responses
- Real-time connection animations

## Architecture

The UI uses the same `AgentSocketClient` APIs as the CLI:
- `subscribe_events()` for real-time monitoring
- `health_check()` for agent status
- Direct MCP calls for chat functionality

This ensures the UI works with any agent configuration and scales dynamically.
