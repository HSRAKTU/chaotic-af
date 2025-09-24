<div align="center">
  <img src="assets/images/logo.png" alt="Chaotic AF Logo" width="200" />
  
  # Chaotic AF
  ### Multi-Agent AI Framework

Build multi-agent systems with ease. Summon any number of agents, connect them in any topology, and equip them with tools. Each agent runs as its own process, communicates over Unix sockets for control, and uses MCP for collaboration. The aim is straightforward: make it simple to orchestrate agent networks of any shape and scale.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Tests: Passing](https://img.shields.io/badge/tests-71%20passing-brightgreen.svg)](tests/)
</div>

---

A Python framework for multi-agent AI systems with bidirectional communication via the Model Context Protocol (MCP).  
Agents expose a small control socket for health, metrics, connect, and shutdown.  
A unified client is used by both the CLI and the library. Designed to grow into a canvas UI and more autonomous coordination.

> Status: early alpha. macOS and Linux supported. Windows requires TCP fallback.

---

## Features

### Core
- Agents run in separate OS processes with a Unix control socket each.
- One unified client for CLI + library: `health`, `metrics`, `connect`, `shutdown`.
- Agent-to-agent communication via MCP. External MCP servers supported by config.
- Process isolation ensures stability and true parallelism.

### Operations
- Health checks with thresholds and auto-recovery (restart limits).
- Graceful shutdown and cleanup.
- Prometheus-compatible metrics.
- Structured logging with correlation IDs.

### Developer Experience
- Simple CLI: start, stop, connect, chat, status, metrics.
- Interactive chat with verbose mode (see agent thinking + arrows).
- YAML configs with validation.
- Unit + integration tests (71 passing).
- Examples for simple, debug, discussion, and full dev team workflows.

---

## Quick Start

### Install
```bash
git clone <your-repo-url>
cd chaotic-af
python -m venv agent_env
source agent_env/bin/activate 
pip install -r requirements.txt
````
Optional for tests:

```bash
pip install -r requirements-test.txt
pytest tests/ -v
```

### Configure API Keys

`.env` in project root:

```
GOOGLE_API_KEY=your-gemini-key
OPENAI_API_KEY=your-openai-key   # optional
ANTHROPIC_API_KEY=your-anthropic-key   # optional
```

### Create Agents

```yaml
# customer_service.yaml
agent:
  name: customer_service
  llm_provider: google
  llm_model: gemini-1.5-pro
  role_prompt: |
    You are a customer service representative.
  port: 9001
logging:
  level: INFO
  file: logs/customer_service.log
```

```yaml
# tech_support.yaml
agent:
  name: tech_support
  llm_provider: google
  llm_model: gemini-1.5-pro
  role_prompt: |
    You are a technical support specialist.
  port: 9002
logging:
  level: INFO
  file: logs/tech_support.log
```

### Run Agents

```bash
python -m agent_framework.cli.commands start customer_service.yaml tech_support.yaml
python -m agent_framework.cli.commands connect customer_service tech_support -b
python -m agent_framework.cli.commands chat customer_service "I need help with billing and Python imports"
python -m agent_framework.cli.commands status
```

Stop:

```bash
python -m agent_framework.cli.commands stop
```

---

## How It Works

```
User / CLI
   |
Supervisor (process manager + registry)
   |
   +-- Unix control sockets per agent (health, metrics, connect, shutdown)
   |
Agents (processes) <—— MCP HTTP endpoints ——> Other Agents / External MCP servers
```

* **Control plane**: Local sockets for lifecycle + monitoring.
* **Work plane**: MCP for tool calls and collaboration.
* **Unified Client**: Both CLI and library use `AgentSocketClient`.

---

## Example Usage (Try it yourself)

To quickly see Chaotic AF in action, spin up a small software team of agents and chat with them.

### 1. Start Example Agents

```bash
rm -f /tmp/chaotic-af/agent-*.sock
python -m agent_framework.cli.commands start \
  examples/ui-specific/product_manager.yaml \
  examples/ui-specific/frontend_dev.yaml \
  examples/ui-specific/backend_dev.yaml \
  examples/ui-specific/tech_lead.yaml \
  examples/ui-specific/qa_tester.yaml
````
<img width="942" height="553" alt="Screenshot 2025-09-25 at 01 15 25" src="https://github.com/user-attachments/assets/16d6cc49-66d3-4f41-9a19-6a3787b0080f" />
Checking Status:
<img width="922" height="196" alt="Screenshot 2025-09-25 at 01 15 55" src="https://github.com/user-attachments/assets/924e0f2f-6741-4c8c-94c5-3e08325faea3" />
### 2. Connect Them

```bash
python -m agent_framework.cli.commands connect product_manager frontend_dev -b
python -m agent_framework.cli.commands connect product_manager backend_dev -b
python -m agent_framework.cli.commands connect backend_dev tech_lead -b
python -m agent_framework.cli.commands connect frontend_dev tech_lead -b
python -m agent_framework.cli.commands connect qa_tester product_manager -b
python -m agent_framework.cli.commands connect qa_tester frontend_dev -b
```
<img width="954" height="280" alt="Screenshot 2025-09-25 at 01 16 16" src="https://github.com/user-attachments/assets/e62f1b08-a3e5-4308-8724-00cca864ba43" />
### 3. Chat with Verbose Mode

```bash
python -m agent_framework.cli.commands chat product_manager -v \
  "We need to add user authentication with social login. How should we approach this?"
```

<img width="1321" height="296" alt="Screenshot 2025-09-25 at 01 17 39" src="https://github.com/user-attachments/assets/b6334d41-857c-4d20-b294-0c13f74f6b28" />

You’ll see product\_manager receive the query, consult frontend\_dev and backend\_dev, and coordinate with tech\_lead and qa\_tester before giving you an answer.

### 4. Interactive Mode

```bash
python -m agent_framework.cli.commands chat product_manager -i -v
```

Type questions directly and watch the agents coordinate in real time.


## CLI Tool Commands

The CLI is the main entry point for local development. Both the CLI and the Python library use the same unified socket client under the hood.

### Current Commands
```bash
# Agent lifecycle
python -m agent_framework.cli.commands start a.yaml b.yaml   # Start agents
python -m agent_framework.cli.commands stop                  # Stop all agents
python -m agent_framework.cli.commands restart a b           # Restart specific agents

# Health and metrics
python -m agent_framework.cli.commands status                # Show agent status
python -m agent_framework.cli.commands health a              # Health check for agent
python -m agent_framework.cli.commands metrics a             # Metrics in JSON/Prometheus

# Connections
python -m agent_framework.cli.commands connect a b           # Connect a → b
python -m agent_framework.cli.commands connect a b -b        # Bidirectional connect

# Chat
python -m agent_framework.cli.commands chat a "Hello"        # Send message
python -m agent_framework.cli.commands chat a -v "Ask b X"   # Verbose mode
python -m agent_framework.cli.commands chat a -i             # Interactive session
````

### ToDos for More Robust Control

* **Idempotent start**: refuse to spawn duplicate agents with the same name.
* **READY handshake**: ensure an agent only reports "running" once its socket is ready.
* **Connection inspection**: `list_connections` and `disconnect` commands to manage topology.
* **Better state commands**: view/update live agent configs, inspect conversation history.
* **Dynamic control**: hot-swap prompts, adjust log levels, toggle tools without restart.
* **Improved error feedback**: actionable messages when agents cannot start or connect.

These improvements will make the CLI a reliable single source of truth for managing agents in real-world workflows.

---
## Handling Zombie Processes

In some cases, agent processes may not shut down cleanly and leave behind "zombie" processes or stray sockets. This can cause errors like agents showing as running when they are not, or failing to start on the same port.

### Diagnose

List all running agent processes:
```bash
ps -ef | grep agent_framework | grep -v grep
````

Check specifically for zombies or defunct processes:

```bash
ps -axo pid,ppid,stat,etime,comm | egrep " Z|defunct" || echo "no zombies"
```

Look for unreaped supervisor logs (optional):

```bash
grep -i reaped supervisor.log || echo "no reaped entries"
```

### Kill Stray Processes

If you see unwanted processes, terminate them:

```bash
kill -9 <PID>
```

### Clean Up Sockets

Remove any leftover control sockets to avoid conflicts:

```bash
rm -f /tmp/chaotic-af/agent-*.sock
```

### Restart Agents

After cleanup, agents can be restarted safely:

```bash
python -m agent_framework.cli.commands start <configs...>
```

---

**Tip**: If you run into repeated zombie issues, ensure you always stop agents with the CLI:

```bash
python -m agent_framework.cli.commands stop
```

instead of closing your terminal or killing the supervisor abruptly.

---
## Current Status & Next Steps

* ✅ Centralized socket client, dynamic tool discovery, event streaming.
* ✅ CLI and library both use the same APIs.
* ✅ Interactive chat with agent-to-agent visibility.
* ✅ Process isolation and health recovery.

### Next Priorities

* Getting started tutorial, API docs, real-world examples.
* Multi-agent chat orchestration, history persistence, exports.
* Web-based dashboard + Grafana templates.
* Scaling to 50+ agents and distributed deployment.
* Developer tooling: VS Code extension, config validation, hot reload.

---

## Contributing

* Fork → branch → PR.
* Keep changes small and tested.
* For issues, include commands, OS, Python version, and logs.

---

## License

MIT. See [LICENSE](LICENSE).

---
