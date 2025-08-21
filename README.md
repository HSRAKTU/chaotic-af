<div align="center">
  <img src="assets/images/logo.png" alt="Chaotic AF Logo" width="200" />
  
  # 🌀 Chaotic AF
  ### Multi-Agent AI Framework
  
  **Spawn agents, connect them in any topology, let them collaborate. Zero CPU overhead. Pure chaos, perfectly orchestrated.**
  
  [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
  [![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
  [![Tests: Passing](https://img.shields.io/badge/tests-71%20passing-brightgreen.svg)](tests/)
</div>

---

A Python framework for building multi-agent AI systems with bidirectional communication via the Model Context Protocol (MCP). Features health monitoring, auto-recovery, metrics collection, and graceful shutdown.

## 🌟 Features

### Core Capabilities
- **Multi-Agent Architecture**: Create networks of specialized AI agents that can communicate and collaborate
- **Any Topology Support**: Star, chain, mesh, or custom connection patterns
- **Zero CPU Overhead**: Unix socket-based IPC with < 1% CPU usage
- **MCP-Based Communication**: Built on the Model Context Protocol for standardized tool calling
- **LLM Agnostic**: Works with OpenAI, Anthropic, Google Gemini, and more (even older models!)
- **Process Isolation**: Each agent runs in its own process for stability and true parallelism

### Advanced Features
- **Health Monitoring**: Automatic health checks with configurable thresholds
- **Auto-Recovery**: Agents automatically restart on failure with configurable limits
- **Graceful Shutdown**: Clean termination via socket commands and signal handling
- **Prometheus Metrics**: Comprehensive metrics collection and export
- **Structured Logging**: Comprehensive logging with agent-specific prefixes and correlation IDs
- **Event Streaming**: Real-time event emission for observability

### Developer Experience
- **Interactive Chat CLI**: Beautiful verbose chat mode showing agent thinking and inter-agent communication
- **Real-time Observability**: See agent-to-agent messages with colored arrows (`agent1 → agent2`, `agent1 ← agent2`)
- **Dynamic Tool Discovery**: Agents automatically discover `communicate_with_<agent>` tools from connected peers
- **Robust CLI**: Rich commands for agent management, monitoring, and debugging
- **Live Monitoring**: Real-time agent status with `agentctl watch`
- **Comprehensive Testing**: 71+ unit and integration tests
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

### 4. Start Your First Agent System

Create agent configs:
```bash
# Create customer_service agent
cat > customer_service.yaml << EOF
agent:
  name: customer_service
  llm_provider: google
  llm_model: gemini-1.5-pro
  role_prompt: |
    You are a friendly customer service representative.
    Your job is to understand customer issues and route them to the right specialist.
    Available specialists: tech_support (technical issues).
    Always be polite and empathetic. Ask clarifying questions if needed.
  port: 9001

logging:
  level: INFO
  file: logs/customer_service.log
EOF

# Create tech_support agent  
cat > tech_support.yaml << EOF
agent:
  name: tech_support
  llm_provider: google
  llm_model: gemini-1.5-pro
  role_prompt: |
    You are a technical support specialist. You help with:
    - Software installation and configuration
    - Bug reports and error messages
    - Performance issues
    - Integration problems
    Provide clear, step-by-step solutions. If you need more info, ask specific technical questions.
  port: 9002

logging:
  level: INFO
  file: logs/tech_support.log
EOF
```

Start agents and test interactive chat:
```bash
# Start agents
python -m agent_framework.cli.commands start customer_service.yaml tech_support.yaml

# Connect them
python -m agent_framework.cli.commands connect customer_service tech_support -b

# Test with interactive chat - see complete agent coordination
python -m agent_framework.cli.commands chat customer_service -v "I need help with Python imports and billing issues"

# Complete agent-to-agent coordination display:
# user → customer_service: I need help with Python imports and billing issues
# [customer_service thinking...]
# customer_service → tech_support: User needs help with Python imports  
# customer_service ← tech_support: Here's how to fix import issues...
# [customer_service thinking...]
# customer_service → billing: User also has billing concerns
# customer_service ← billing: I can help with billing questions...
# user ← customer_service: I've coordinated with our teams...
```

### 5. Advanced UI Demo (Most Impressive!)

**7-Agent Software Development Team with Real-Time Monitoring:**
```bash
# Start the impressive 7-agent software team demo
cd examples/ui-specific
./setup_dev_team.sh

# Start beautiful UI monitor with animations
pip install -r requirements-ui.txt
python ../../ui_server.py

# Open: http://localhost:8080
# Test complex scenarios like:
# "Implement user authentication with social login - coordinate with entire team"
# Watch agents coordinate across departments with beautiful animations!
```

### 6. Other Demos

```bash
# Simple demo - basic agent communication
python examples/simple.py

# Debug demo - see all tool calls and responses
python examples/debug.py

# Discussion demo - multi-agent collaboration
python examples/discussion.py

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
│   ├── agent.py           # Main Agent class with tool handling
│   ├── config.py          # Configuration handling
│   ├── llm.py             # LLM abstraction layer
│   ├── events.py          # Event streaming system with race-condition fixes
│   └── logging.py         # Structured logging
├── mcp/
│   ├── server_universal.py # Universal MCP server with dynamic tool discovery
│   └── client.py          # MCP client with communicate_with_<agent> tools
├── client/
│   └── socket_client.py   # Centralized socket communication (NEW)
├── network/
│   ├── supervisor.py      # Process management with health monitoring
│   ├── agent_runner.py    # Individual agent runner
│   ├── connection_manager.py # Dynamic connection management
│   └── control_socket.py  # Unix socket control interface
└── cli/
    └── commands.py        # Full CLI with interactive chat support
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

Agents discover and use tools from other connected agents automatically:
- **Dynamic Tool Discovery**: When agents connect, they can see each other's `communicate_with_<agent_name>` tools
- **Direct MCP Communication**: No proxy tools - agents call each other's MCP servers directly
- **Bidirectional**: Both agents can communicate with each other once connected
- **Chat Interface**: Use `chat_with_user` tool for direct human interaction

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
python -m agent_framework.cli.commands start agent1.yaml agent2.yaml  # Start agents
python -m agent_framework.cli.commands stop alice                     # Stop specific agent
python -m agent_framework.cli.commands stop                           # Stop all agents
python -m agent_framework.cli.commands restart alice bob              # Restart specific agents
python -m agent_framework.cli.commands restart                        # Restart all agents

# Interactive Chat (NEW!)
python -m agent_framework.cli.commands chat alice "Hello!"            # Send message to alice
python -m agent_framework.cli.commands chat alice -v "Ask bob about X" # Verbose mode - see agent thinking
python -m agent_framework.cli.commands chat alice -i                  # Interactive chat session
python -m agent_framework.cli.commands chat alice -i -v               # Interactive + verbose

# Monitoring and debugging
python -m agent_framework.cli.commands status                         # Show agent status
python -m agent_framework.cli.commands watch                          # Live monitoring (like htop)
python -m agent_framework.cli.commands logs alice -f                  # Follow agent logs
python -m agent_framework.cli.commands health alice                   # Check agent health via socket
python -m agent_framework.cli.commands metrics alice                  # Get agent metrics
python -m agent_framework.cli.commands metrics alice -f prometheus    # Get metrics in Prometheus format

# Agent connections
python -m agent_framework.cli.commands connect alice bob              # Connect alice → bob
python -m agent_framework.cli.commands connect alice bob -b           # Bidirectional connection

# Utilities
python -m agent_framework.cli.commands init                           # Create agent template
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

- [Architecture Details](docs/ARCHITECTURE.md) - Detailed architecture and MCP protocol usage
- [Current Status](docs/CURRENT_STATUS.md) - Development progress and feature completeness
- [Implementation Specs](docs/IMPLEMENTATION_SPECS.md) - Technical implementation details
- [Known Issues](docs/KNOWN_ISSUES.md) - Current limitations and resolved issues
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