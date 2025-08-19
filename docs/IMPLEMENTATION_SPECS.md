# Agent Framework Implementation Specifications

## Project Overview
**Goal**: Build a Python framework for creating multi-agent AI systems where agents communicate via the Model Context Protocol (MCP).

**Key Innovation**: Each agent is both an MCP server (to receive communications) and an MCP client (to reach out to others), creating a peer-to-peer agent network.

## Architecture Decisions

### 1. Core Abstraction: The Agent Node
Each agent consists of:
- **LLM Provider**: Brain of the agent (supports OpenAI, Anthropic, Google)
- **Master MCP Server**: Exposes tools for other agents to communicate with this agent
- **Master MCP Client**: Connects to other agents and external MCP tools
- **Event Stream**: Emits structured events for future UI integration
- **Logger**: Agent-prefixed structured logging for debugging

### 2. Process Architecture
- **One Process Per Agent**: Each agent runs in its own OS process
- **Why**: Process isolation, no GIL issues, clean crashes, true parallelism
- **Supervisor Pattern**: Central supervisor manages agent lifecycles
- **Communication**: Agents communicate via HTTP/SSE transport (always-on)

### 3. MCP Protocol Usage
- **Server Tools Exposed**:
  - `communicate_with_agent`: Primary inter-agent communication
  - `get_agent_status`: Health checks and capability discovery
  - `chat_with_user`: Direct human interaction interface
- **Client Capabilities**:
  - Connect to other agents dynamically
  - Connect to external MCP tools (web search, databases, etc.)

### 4. Tool Calling for ANY LLM
**Problem**: Older LLMs (GPT-3, Claude-1) don't have native function calling
**Solution**: Prompt engineering with XML tags

```python
# For older models, inject this prompt:
To use a tool, respond with:
<tool_use>
{"tool": "tool_name", "parameters": {...}}
</tool_use>
```

The framework parses these tags and executes tool calls, making ANY LLM capable of tool use.

### 5. State Management
- **Conversation State**: Stored in MCP session objects
- **Agent Identity**: System prompt makes each agent aware of:
  - Its role in the multi-agent system
  - Other available agents
  - How to communicate with peers

### 6. Logging Architecture
Structured logging with correlation IDs:
```
[2024-01-10 10:23:45.123] [RESEARCHER] [TOOL_CALL_RECEIVED] communicate_with_agent
  From: coordinator
  Payload: {"message": "Find papers on AGI"}
  Correlation ID: 123e4567-e89b-12d3-a456-426614174000
```

## Implementation Status

### ✅ Completed Modules

1. **Core Configuration** (`core/config.py`)
   - YAML-based agent configuration
   - Environment variable management for API keys
   - Typed configuration objects with validation

2. **LLM Abstraction** (`core/llm.py`)
   - Unified interface for OpenAI, Anthropic, Google
   - Tool calling for ANY model (native or prompt-based)
   - Response parsing with tool call extraction

3. **Event System** (`core/events.py`)
   - Structured event emission for all agent actions
   - Event history for debugging
   - Real-time streaming for observability

4. **Logging System** (`core/logging.py`)
   - Agent-prefixed structured logs
   - Tool call tracking with payloads
   - File and console output with colors

5. **Universal MCP Server** (`mcp/server_universal.py`)
   - Dynamic agent connections via `contact_agent`
   - No hardcoded agent names
   - Conversation context management
   - Handles both agent and user interactions

6. **Master MCP Client** (`mcp/client.py`)
   - Manages dynamic connections to other agents
   - Handles connection failures gracefully
   - Supports external MCP tools
   - Thread-safe connection management

7. **Agent Core** (`core/agent.py`)
   - Integrates all components
   - Handles LLM tool calls
   - Manages agent lifecycle
   - Metrics collection integration

8. **Control Socket** (`network/control_socket.py`)
   - Zero-CPU Unix socket control plane
   - JSON protocol for commands
   - Health, connect, shutdown, metrics commands
   - Clean socket cleanup on exit

9. **Health Monitoring** (`core/health.py`)
   - Automatic health checks every 5 seconds
   - Configurable failure thresholds
   - Auto-recovery with restart limits
   - Restart tracking (max 5 per hour)

10. **Metrics Collection** (`core/metrics.py`)
    - Prometheus-compatible metrics
    - Agent uptime, message counts, latencies
    - Exposed via socket commands
    - Standard Prometheus text format

11. **Process Supervisor** (`network/supervisor.py`)
    - Starts agents as separate processes
    - Integrated health monitoring
    - Graceful shutdown management
    - Connection orchestration

12. **CLI Interface** (`cli/commands.py`)
    - Full lifecycle: `start/stop/restart`
    - Monitoring: `status/watch/health/metrics`
    - Connections: `connect` with bidirectional support
    - Debugging: `logs -f`, `init`

### ✅ Recent Updates

1. **Gemini/Google AI Support**
   - Implemented `GoogleProvider` class in `core/llm.py`
   - Full support for Gemini models with native function calling
   - Handles Gemini's unique message format (no system role)
   - Tool calling works with both native and prompt-based approaches

2. **Three-Agent Example Created**
   - **Researcher**: Gemini-powered agent for information gathering
   - **Writer**: Gemini-powered agent for content creation
   - **Coordinator**: Gemini-powered orchestrator agent
   - All configured to work with single GOOGLE_API_KEY from .env

3. **Testing Scripts**
   - `simple_test.py`: Basic connectivity and communication tests
   - `demo.py`: Full demonstration of agents collaborating on a task
   - Shows real-time event monitoring and structured logging

### 🚧 Next Steps

1. **Install dependencies and test the system**
2. **Run the three-agent demo**
3. **Add more sophisticated agent behaviors**
4. **Implement external MCP tool servers**

## Design Patterns Used

1. **Decorator Pattern**: MCP tools defined via decorators
2. **Observer Pattern**: Event streaming system
3. **Supervisor Pattern**: Process management
4. **Factory Pattern**: LLM provider creation
5. **Context Manager**: Resource lifecycle (connections)

## Key Technical Decisions

1. **Why FastMCP?**: Simpler API than official SDK, built-in server capabilities
2. **Why Process Isolation?**: Stability, true parallelism, clean failures
3. **Why HTTP Transport?**: Always-on connections, firewall friendly
4. **Why YAML Config?**: Human readable, industry standard
5. **Why Structured Logging?**: Debugging multi-agent systems is complex

## Challenges Solved

1. **Tool Calling for Old LLMs**: Clever prompt engineering with XML parsing
2. **Process Management**: Supervisor pattern with health monitoring
3. **Dynamic Connections**: Agents can discover and connect at runtime
4. **Observability**: Every action is logged and emitted as events

## Production Architecture

### Control Plane (Unix Sockets)
- Zero-CPU event-driven control
- Health checks, metrics, connections
- Graceful shutdown handling
- No interference with data plane

### Data Plane (MCP/HTTP)
- Agent-to-agent communication
- Tool execution
- LLM interactions
- Standard MCP protocol

### Monitoring & Recovery
- Automatic health checks
- Configurable auto-recovery
- Prometheus metrics export
- Comprehensive logging

## Configuration Example

```yaml
agent:
  name: researcher
  llm_provider: anthropic
  llm_model: claude-3-opus-20240229
  role_prompt: |
    You are a research assistant specialized in finding information.
  port: 8001

external_mcp_servers:
  - name: web_search
    url: http://localhost:9001/sse

logging:
  level: INFO
  file: logs/researcher.log
```

## API Usage

```python
# Programmatic usage
from agent_framework import Agent, AgentConfig, AgentSupervisor

# Create supervisor
supervisor = AgentSupervisor()

# Add agents
supervisor.add_agent(config1)
supervisor.add_agent(config2)

# Start all
await supervisor.start_all()
```

## Testing Strategy

1. **Unit Tests**: Individual component testing
2. **Integration Tests**: Agent communication tests
3. **System Tests**: Full 3-agent scenario
4. **Observability Tests**: Verify logging/events

## Development Diary

### Session 1: Initial Implementation (Completed)
- Built complete framework architecture
- Implemented all core modules (config, LLM, events, logging)
- Created Master MCP Server/Client for each agent
- Built process supervisor for agent lifecycle management
- Implemented CLI with intuitive commands
- Full observability with structured logging and events

### Session 2: Gemini Support & Testing Setup (Current)
- **Added Gemini/Google AI Provider**: 
  - Full implementation with native function calling
  - Handles Gemini's message format quirks
  - Tested tool calling capability
- **Created Three-Agent Example**:
  - All agents use Gemini (gemini-1.5-pro)
  - Researcher, Writer, Coordinator roles defined
  - Configured for collaborative content creation
- **Testing Infrastructure**:
  - simple_test.py for basic verification
  - demo.py for full collaborative demonstration
  - README with clear instructions
- **Environment Setup**:
  - requirements.txt for dependency management
  - .env file for API keys (single key for all agents)
  - Virtual environment ready

### Ready for Testing
The system is now ready for:
1. `pip install -r requirements.txt`
2. Add GOOGLE_API_KEY to .env
3. Run `python examples/three_agents/simple_test.py` to verify
4. Run `python examples/three_agents/demo.py` for full demo

### Session 3: Architecture Refinement (Completed)
- **Solved Event Loop Conflict**:
  - Initial approach used subprocess for MCP server (complex)
  - Discovered FastMCP's `run_async()` method
  - Simplified to single process per agent
- **Implemented Tool Execution**:
  - MCP server can now execute tool calls
  - Proper ReAct pattern implementation
  - Agents can communicate via tools
- **Two-Phase Startup**:
  - Phase 1: Start all MCP servers
  - Phase 2: Connect agents to each other
  - Ensures no connection attempts before servers are ready

## Final Architecture

### Design
- **One Process Per Agent**: Clean separation, managed by supervisor
- **FastMCP run_async()**: No event loop conflicts
- **Direct Tool Execution**: MCP server has access to agent's MCP client
- **Robust Communication**: Agents can call tools on each other

### Tool Execution Flow
1. Agent receives message (via MCP tool)
2. LLM decides what tools to use
3. MCP server executes tools via agent's client
4. Results fed back to LLM
5. Continue until final response

### Session 4: Socket Infrastructure & CPU Fix (Completed)
- **Implemented Unix Socket Control**:
  - Zero-CPU control plane via `/tmp/chaotic-af/agent-{name}.sock`
  - JSON protocol for health, connect, shutdown commands
  - CPU usage reduced from 80-100% to < 1%
- **Fixed CLI Connect Command**:
  - Now actually sends commands to agents
  - Bidirectional connections work properly
  - Socket-first, stdin fallback architecture
- **Comprehensive Testing**:
  - Added socket mode tests
  - Verified CPU usage improvements
  - All integration tests passing

### Session 5: Production Features (Completed)
- **Graceful Shutdown**:
  - Socket command → SIGTERM → SIGKILL sequence
  - Proper cleanup of resources
  - Socket file removal on exit
- **Health Monitoring System**:
  - Automatic checks every 5 seconds
  - Configurable failure thresholds
  - Auto-recovery with restart limits (5/hour)
- **Prometheus Metrics**:
  - Full metrics collection
  - Exposed via socket commands
  - Standard Prometheus text format
- **Enhanced CLI Commands**:
  - `watch` - Live monitoring like htop
  - `health` - Check agent health
  - `metrics` - Get Prometheus metrics
  - `restart` - Graceful restart
- **Test Suite Updates**:
  - Fixed all unit tests (44 passing)
  - Updated integration tests (23 passing)
  - Total: 67 tests, 100% passing

### Status
✅ Production-ready with zero-CPU overhead
✅ Comprehensive monitoring and recovery
✅ All tests passing (67/67)
✅ Full CLI with rich commands
✅ Prometheus metrics integration

---
*Last Updated: Production features complete*
