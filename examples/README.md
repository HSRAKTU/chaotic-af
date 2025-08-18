# Chaotic AF Examples

This directory contains examples showing different ways to use the Chaotic AF agent framework.

## Examples

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
