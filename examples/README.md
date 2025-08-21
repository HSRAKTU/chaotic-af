# Chaotic AF Examples

This directory contains examples showing different ways to use the Chaotic AF agent framework.

## Quick Start Example

### Interactive Chat Demo
```bash
# 1. Create two simple agents
cat > customer_service.yaml << EOF
agent:
  name: customer_service
  llm_provider: google
  llm_model: gemini-1.5-pro
  role_prompt: |
    You are a friendly customer service representative.
    Route technical issues to tech_support using communicate_with_tech_support.
  port: 9001
logging:
  level: INFO
  file: logs/customer_service.log
EOF

cat > tech_support.yaml << EOF
agent:
  name: tech_support
  llm_provider: google
  llm_model: gemini-1.5-pro
  role_prompt: |
    You are a technical support specialist.
    Provide clear, step-by-step solutions for technical problems.
  port: 9002
logging:
  level: INFO
  file: logs/tech_support.log
EOF

# 2. Start and connect agents
python -m agent_framework.cli.commands start customer_service.yaml tech_support.yaml
python -m agent_framework.cli.commands connect customer_service tech_support -b

# 3. Chat interactively with beautiful verbose mode
python -m agent_framework.cli.commands chat customer_service -v "I'm having Python import errors"

# Watch agent thinking and communication:
# [customer_service thinking...]
# customer_service → tech_support: User is having Python import errors...
# customer_service ← tech_support: Here's how to fix import errors...
```

## Featured Demo

### 🎨 **UI-Specific: Software Development Team** (`ui-specific/`)
**Most Impressive Demo** - 7-agent software development team with complex coordination:
- Product Manager, Backend Dev, Frontend Dev, DevOps, QA, Security, Tech Lead
- Realistic business automation workflow
- Hybrid network topology (star + mesh + integration points)
- Beautiful real-time animations with flowing message dots
- Complete chaos mode - any agent can coordinate with any other agent

```bash
cd examples/ui-specific
./setup_dev_team.sh      # Start 7 agents with complex topology
python ../../ui_server.py # Start UI monitor
# Open: http://localhost:8080 and test complex scenarios!
```

## All Examples

### 1. Library Usage (`library_usage.py`)
Shows how to use Chaotic AF as a Python library:
- Creating agents programmatically
- Starting agents with socket mode (< 1% CPU)
- Connecting agents dynamically
- Sending messages between agents
- Clean shutdown

Run it:
```bash
python examples/library_usage.py
```

### 2. CLI Usage (`cli_usage/`)
Demonstrates the command-line interface:
- YAML configuration files
- Starting multiple agents
- Dynamic connections
- Status monitoring
- Interactive chat features

Run it:
```bash
cd examples/cli_usage
./demo.sh
```

### 3. Simple Demo (`simple.py`)
Minimal example with two agents:
- Basic agent communication
- Minimal logging
- Quick test of functionality

### 4. Debug Demo (`debug.py`)
Same as simple but with verbose logging:
- See all tool calls
- Debug message flow
- Troubleshooting aid

### 5. Discussion Demo (`discussion.py`)
Three agents in a collaborative discussion:
- Complex multi-agent interaction
- Bidirectional connections
- Emergent behavior

### 6. Dynamic Demo (`dynamic.py`)
Showcases dynamic connection capabilities:
- Runtime connection changes
- Flexible agent topologies

## Key Features Demonstrated

1. **Zero CPU Overhead**: All examples use socket mode by default
2. **Dynamic Connections**: Agents can connect/disconnect at runtime
3. **Multiple LLMs**: Examples work with Google, OpenAI, Anthropic
4. **Clean Architecture**: Proper startup and shutdown
5. **Real Communication**: Agents actually talk to each other via MCP

## Requirements

Set your API keys in `.env`:
```bash
GOOGLE_API_KEY=your-key-here
OPENAI_API_KEY=your-key-here  # Optional
ANTHROPIC_API_KEY=your-key-here  # Optional
```

Most examples use Google's Gemini by default as it has a generous free tier.
