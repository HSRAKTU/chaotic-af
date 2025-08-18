<div align="center">
  <img src="assets/images/logo.png" alt="Chaotic AF Logo" width="200" />
  
  # 🌀 Chaotic AF
  ### AI Swarm Framework
  
  **Spawn agents, connect them however you want, let them talk. That's it. Pure chaos.**
  
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
</div>

---

A Python framework for building multi-agent AI systems with bidirectional communication via the Model Context Protocol (MCP).

> **Note**: This is a proof-of-concept implementation showcasing MCP-based agent-to-agent communication.

## 🌟 Features

- **Multi-Agent Architecture**: Create networks of specialized AI agents that can communicate and collaborate
- **MCP-Based Communication**: Built on the Model Context Protocol for standardized tool calling
- **LLM Agnostic**: Works with OpenAI, Anthropic, Google Gemini, and more (even older models!)
- **Process Isolation**: Each agent runs in its own process for stability and true parallelism
- **Structured Logging**: Comprehensive logging with agent-specific prefixes and correlation IDs
- **Event Streaming**: Real-time event emission for future UI integration
- **CLI Management**: Simple commands to start, stop, and monitor agents
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
```

### 2. Set Up API Keys

Create a `.env` file in the project root:

```env
# API Keys for LLM Providers
GOOGLE_API_KEY=your-gemini-api-key-here
OPENAI_API_KEY=your-openai-key-here  # Optional
ANTHROPIC_API_KEY=your-anthropic-key-here  # Optional
```

### 3. Run Example Demos

```bash
# Simple demo - basic agent communication
python examples/simple.py

# Debug demo - see all tool calls and responses
python examples/debug.py

# Discussion demo - military-style multi-agent discussion
python examples/discussion.py

# Dynamic demo - showcase dynamic connection capabilities
python examples/dynamic.py
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
│   ├── supervisor.py      # Process management
│   ├── agent_runner.py    # Individual agent runner
│   └── connection_manager.py # Dynamic connections
└── cli/
    └── commands.py        # CLI interface (planned)
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
agentctl start agent1.yaml agent2.yaml  # Start agents
agentctl status                         # Show agent status
agentctl logs alice -f                  # Follow agent logs
agentctl stop alice                     # Stop specific agent
agentctl stop                           # Stop all agents
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

## 🚧 Future Enhancements

- [ ] Web UI for visual debugging
- [ ] Agent persistence and state management
- [ ] Distributed deployment across machines
- [ ] Authentication and security
- [ ] Prometheus metrics integration
- [ ] More LLM provider integrations

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