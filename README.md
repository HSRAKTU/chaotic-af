<div align="center">
  <img src="assets/images/logo.png" alt="Chaotic AF Logo" width="200" />
  
  # 🌀 Chaotic AF
  ### Production-Ready Multi-Agent AI Framework
  
  **Spawn agents, connect them in any topology, let them collaborate. Zero CPU overhead. Pure chaos, perfectly orchestrated.**
  
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
  [![Tests: Passing](https://img.shields.io/badge/tests-67%20passing-brightgreen.svg)](tests/)
</div>

---

A production-ready Python framework for building robust multi-agent AI systems with bidirectional communication via the Model Context Protocol (MCP). Features health monitoring, auto-recovery, metrics collection, and graceful shutdown.

## 🌟 Features

### Core Capabilities
- **Multi-Agent Architecture**: Create networks of specialized AI agents that can communicate and collaborate
- **Any Topology Support**: Star, chain, mesh, or custom connection patterns
- **Zero CPU Overhead**: Unix socket-based IPC with < 1% CPU usage
- **MCP-Based Communication**: Built on the Model Context Protocol for standardized tool calling
- **LLM Agnostic**: Works with OpenAI, Anthropic, Google Gemini, and more (even older models!)
- **Process Isolation**: Each agent runs in its own process for stability and true parallelism

### Production Features
- **Health Monitoring**: Automatic health checks with configurable thresholds
- **Auto-Recovery**: Agents automatically restart on failure with configurable limits
- **Graceful Shutdown**: Clean termination via socket commands and signal handling
- **Prometheus Metrics**: Production-ready metrics collection and export
- **Structured Logging**: Comprehensive logging with agent-specific prefixes and correlation IDs
- **Event Streaming**: Real-time event emission for observability

### Developer Experience
- **Robust CLI**: Rich commands for agent management, monitoring, and debugging
- **Live Monitoring**: Real-time agent status with `agentctl watch`
- **Comprehensive Testing**: 67+ unit and integration tests
- **Bidirectional Connections**: Agents can both provide and consume services

## 🚀 Quick Start

### 1. Install Dependencies

```bash
# Clone the repository
git clone <your-repo-url>
cd chaotic-af

# Create virtual environment
python -m venv agent_env
source agent_env/bin/activate  # On Windows: agent_env\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies (for testing)
pip install -r requirements-test.txt
```

### 2. Run Tests (Optional)

```bash
# Run all tests
pytest tests/ -v

# Run unit tests only (fast)
pytest tests/unit/ -v

# Run integration tests only (slower)
pytest tests/integration/ -v

# Run with coverage
pytest tests/ --cov=agent_framework --cov-report=html
```

### 3. Set Up API Keys

Create a `.env` file in the project root:

```env
# API Keys for LLM Providers
GOOGLE_API_KEY=your-gemini-api-key-here
OPENAI_API_KEY=your-openai-key-here  # Optional
ANTHROPIC_API_KEY=your-anthropic-key-here  # Optional
```

### 4. Run Example Demos

```bash
# Simple demo - basic agent communication
python examples/simple.py

# Debug demo - see all tool calls and responses
python examples/debug.py

# Discussion demo - military-style multi-agent discussion
python examples/discussion.py

# Dynamic demo - showcase dynamic connection capabilities
python examples/dynamic.py

# CLI usage demo - demonstrates all CLI commands
cd examples/cli_usage && ./demo.sh

# Library usage - programmatic agent management
python examples/library_usage.py
```

## 📖 How It Works

### Agent Architecture

Each agent consists of:
- **LLM Brain**: The AI model (Gemini, GPT-4, Claude, etc.)
- **MCP Server**: Exposes tools for other agents to call
- **MCP Client**: Calls tools on other agents
- **Event Stream**: Emits events for observability

### Core Components

```
agent_framework/
├── core/
│   ├── agent.py           # Main Agent class
│   ├── config.py          # Configuration handling
│   ├── llm.py             # LLM abstraction layer
│   ├── events.py          # Event streaming system
│   └── logging.py         # Structured logging
├── mcp/
│   ├── server_universal.py # Universal MCP server
│   └── client.py          # MCP client implementation
├── network/
│   ├── supervisor.py      # Process management with health monitoring
│   ├── agent_runner.py    # Individual agent runner
│   ├── connection_manager.py # Dynamic connection management
│   └── control_socket.py  # Unix socket control interface
└── cli/
    └── commands.py        # Full-featured CLI interface
```

## 🛠️ Creating Your Own Agents

### 1. Define Agent Configuration (YAML)

```yaml
agent:
  name: my_agent
  llm_provider: google  # or openai, anthropic
  llm_model: gemini-1.5-pro
  role_prompt: |
    You are a specialized agent that...
  port: 8004

external_mcp_servers: []  # Optional external tools

logging:
  level: INFO
  file: logs/my_agent.log
```

### 2. Start Your Agent

```python
from agent_framework import AgentSupervisor, AgentConfig

supervisor = AgentSupervisor()

# From YAML
config = AgentConfig.from_yaml("path/to/my_agent.yaml")
supervisor.add_agent(config)

# Or directly
agent = AgentConfig(
    name="my_agent",
    port=8004,
    llm_provider="google",
    llm_model="gemini-1.5-pro",
    role_prompt="You are a specialized agent that..."
)
supervisor.add_agent(agent)

# Start all agents
await supervisor.start_all()
```

### 3. Connect Agents

Each agent exposes these tools:
- `contact_agent`: Send messages to other connected agents
- `get_connections`: List available agent connections
- `get_agent_status`: Check agent health
- `chat_with_user`: Direct human interaction

## 🔍 Example Usage

### Simple Agent Communication
```python
from agent_framework import AgentSupervisor, AgentConfig

# Create supervisor
supervisor = AgentSupervisor()

# Define agents
alice = AgentConfig(
    name="alice",
    port=6001,
    llm_provider="google",
    llm_model="gemini-1.5-pro",
    role_prompt="You are Alice, a helpful assistant."
)

bob = AgentConfig(
    name="bob",
    port=6002,
    llm_provider="google",
    llm_model="gemini-1.5-pro",
    role_prompt="You are Bob, an expert in geography."
)

# Add and start agents
supervisor.add_agent(alice)
supervisor.add_agent(bob)
await supervisor.start_all()

# Connect agents
await supervisor.connect("alice", "bob")
```

## 📊 Monitoring & Debugging

### Logs
- Each agent logs to its own file
- Structured format with timestamps and correlation IDs
- Tool calls are logged with payloads and responses

### CLI Commands

```bash
# Agent lifecycle management
agentctl start agent1.yaml agent2.yaml  # Start agents
agentctl stop alice                     # Stop specific agent
agentctl stop                           # Stop all agents
agentctl restart alice bob              # Restart specific agents
agentctl restart                        # Restart all agents

# Monitoring and debugging
agentctl status                         # Show agent status
agentctl watch                          # Live monitoring (like htop)
agentctl logs alice -f                  # Follow agent logs
agentctl health alice                   # Check agent health via socket
agentctl metrics alice                  # Get agent metrics
agentctl metrics alice -f prometheus    # Get metrics in Prometheus format

# Agent connections
agentctl connect alice bob              # Connect alice → bob
agentctl connect alice bob -b           # Bidirectional connection

# Utilities
agentctl init                           # Create agent template
```

## 🎯 Key Features Explained

### Tool Calling for Any LLM
Even older models without native function calling can use tools through clever prompt engineering:

```python
# For older models, we inject:
"To use a tool, respond with:
<tool_use>
{\"tool\": \"tool_name\", \"parameters\": {...}}
</tool_use>"
```

### Process Isolation
- Each agent runs in its own OS process
- No GIL issues, true parallelism
- Clean crash isolation
- Resource tracking per agent

### Event Streaming
All agent actions emit structured events:
- Tool calls made/received
- Messages sent/received
- Reasoning steps
- Errors and status changes

## 📊 Current Capabilities

### What You Can Build
- **Multi-agent research teams**: Agents with different expertise collaborating
- **Customer service networks**: Specialized agents handling different domains
- **Code review systems**: Agents analyzing different aspects of code
- **Creative writing collaborations**: Agents with different writing styles
- **Data processing pipelines**: Agents transforming data in stages

### Topology Examples
- **Star**: Central coordinator agent connected to specialist agents
- **Chain**: Sequential processing (A → B → C → D)
- **Mesh**: Fully connected network for maximum flexibility
- **Hierarchical**: Manager agents coordinating worker agents

## 📚 Documentation

- [Implementation Specs](docs/IMPLEMENTATION_SPECS.md) - Detailed architecture and design decisions
- [Current Status](docs/CURRENT_STATUS.md) - Development progress and notes
- [UI Design Spec](docs/UI_DESIGN_SPEC.md) - Plans for monitoring UI

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## ⚠️ Known Issues

See [KNOWN_ISSUES.md](docs/KNOWN_ISSUES.md) for current limitations and workarounds.

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

Built with ❤️ using FastMCP and the Model Context Protocol