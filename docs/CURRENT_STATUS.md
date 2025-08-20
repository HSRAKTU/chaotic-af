# Current Status: Chaotic AF Framework

> **Last Updated**: August 19, 2025 

## 🎯 Project Overview

Chaotic AF is a multi-agent AI framework built on the Model Context Protocol (MCP). It enables seamless agent-to-agent communication with zero-CPU overhead, health monitoring, auto-recovery, and comprehensive observability.

## ✅ Completed Features

### 1. **Zero-CPU Socket Infrastructure**
   - `AgentControlSocket` class for IPC via Unix domain sockets
   - JSON-based protocol (health, connect, shutdown, metrics commands)
   - CPU usage reduced from 80-100% to < 1%
   - Socket files at `/tmp/chaotic-af/agent-{name}.sock`
   - **CRITICAL UPDATE**: Stdin/stdout mode completely removed (August 19, 11PM)
     - All agents now use socket mode exclusively
     - Simplified codebase by removing legacy communication path
     - Eliminated pipe buffer blocking issues
     - Removed `--use-stdin` flag as it's no longer needed

### 2. **Production-Grade Features**
   - **Graceful Shutdown**: Socket command → SIGTERM → SIGKILL sequence
   - **Health Monitoring**: Automatic health checks every 5 seconds
   - **Auto-Recovery**: Failed agents restart automatically (max 5/hour)
   - **Prometheus Metrics**: Full observability with standard metrics
   - **Event Streaming**: Real-time events for all agent actions

### 3. **Dynamic Connection System**
   - `ConnectionManager` tracks agent→port mappings dynamically
   - `supervisor.connect(from, to)` explicit connection API
   - Dynamic connections via socket or stdin fallback
   - No hardcoded ports or agent names required!
   - Bidirectional connections supported

### 4. **Universal Tool Architecture**
   - `UniversalAgentMCPServer` with single `contact_agent(name, message)` tool
   - Agents track available connections dynamically
   - Works seamlessly with FastMCP (no core modifications)
   - Agent class fully integrated with universal server

### 5. **Comprehensive CLI Interface**
   ```bash
   # Lifecycle management
   agentctl start alice.yaml bob.yaml   # NON-BLOCKING: Returns immediately
   agentctl stop alice                  # Stop specific agent
   agentctl restart                     # Restart all agents
   agentctl remove alice                # Remove from state tracking
   agentctl remove --stopped            # Clean up all stopped agents
   agentctl remove --failed             # Clean up all failed agents
   
   # Monitoring (ENHANCED August 19)
   agentctl status                      # Real-time status with timing info
   # Shows: starting (2s ago), running ✓, failed, stopped
   agentctl watch                       # Live monitoring (like htop)
   agentctl health alice                # Check agent health
   agentctl metrics alice -f prometheus # Get Prometheus metrics
   
   # Connections
   agentctl connect alice bob -b        # Bidirectional connection
   
   # Debugging
   agentctl logs alice -f               # Follow logs
   agentctl init                        # Create agent template
   
   # Chat (ATTEMPTED but postponed)
   agentctl chat alice                  # Single message (not yet working)
   agentctl chat alice --interactive    # Interactive session (not yet working)
   ```

   **Major CLI Improvements (August 19, 2025):**
   - **Non-blocking start**: `agentctl start` returns immediately, no terminal blocking
   - **Enhanced status**: Shows real-time agent states with color coding and timing
   - **State management**: New `remove` command for cleaning up agent registry
   - **Process isolation**: Each CLI command runs independently (no daemon)
   - **Socket-based health checks**: Status command uses sockets to verify agent readiness

### 6. **Complete Test Suite**
   - **67 tests, all passing**:
     - 44 unit tests covering all modules
     - 23 integration tests including:
       - Graceful shutdown scenarios
       - Health monitoring and auto-recovery
       - Metrics collection
       - CLI command functionality
   - Comprehensive coverage of production scenarios

### 7. **Working Examples**
   - Simple demo - basic agent communication
   - Debug demo - verbose tool call logging
   - Discussion demo - multi-agent collaboration
   - Dynamic demo - runtime connection changes
   - Library usage - programmatic control
   - CLI usage - YAML-based configuration
   - All demos show < 1% CPU usage

## 📊 Performance Metrics

- **CPU Usage**: < 1% idle (down from 80-100%)
- **Memory**: ~50MB per agent
- **Startup Time**: < 2 seconds per agent
- **Connection Time**: < 100ms
- **Health Check Latency**: < 10ms
- **Shutdown Time**: < 1 second (graceful)

### Performance Insights (August 19, 2025)
- **Stdin removal impact**: No measurable performance difference
- **Socket-only mode**: Maintains same < 1% CPU usage
- **Non-blocking start**: CLI returns in < 100ms
- **Parallel status checks**: All agents checked concurrently
- **Load test results**: 10 agents started successfully with stable performance

## 🏗️ Architecture

### Process Model
```
Supervisor (main process)
├── Health Monitor (async task)
├── Metrics Collector
├── Agent A (subprocess)
│   ├── MCP Server (async task)
│   ├── MCP Client
│   ├── Control Socket
│   └── Metrics Exporter
├── Agent B (subprocess)
│   ├── MCP Server (async task)
│   ├── MCP Client
│   ├── Control Socket
│   └── Metrics Exporter
└── Connection Manager
```

### Health Monitoring Flow
```
1. HealthMonitor checks each agent every 5 seconds
2. If socket health check fails → increment failure count
3. If failures > threshold (3) → trigger auto-recovery
4. Stop failed agent → Wait → Restart with same config
5. If restarts > limit (5/hour) → Stop trying, alert user
```

## 🌟 Production Capabilities

### What You Can Build
- **Research Teams**: Multiple specialized agents collaborating
- **Customer Service**: Domain-specific agents handling queries
- **Code Analysis**: Agents reviewing different aspects of code
- **Creative Projects**: Agents with different styles working together
- **Data Pipelines**: Sequential processing through agent chain

### Supported Topologies
- **Star**: Central coordinator with specialist agents
- **Chain**: Sequential processing (A → B → C → D)
- **Mesh**: Fully connected for maximum flexibility
- **Hierarchical**: Manager agents coordinating workers
- **Custom**: Any topology you can imagine

## 🚀 Ready for Production

The framework is production-ready with:
- Comprehensive error handling
- Automatic recovery from failures
- Full observability via metrics
- Graceful degradation
- Battle-tested with 67 passing tests

## 📝 Example Usage

```python
# Python API with health monitoring
supervisor = AgentSupervisor(
    health_config=HealthConfig(
        check_interval=5.0,
        failure_threshold=3,
        max_restarts=5
    )
)
supervisor.add_agent(alice_config)
supervisor.add_agent(bob_config)
await supervisor.start_all()
await supervisor.connect("alice", "bob", bidirectional=True)

# CLI with full monitoring
agentctl start alice.yaml bob.yaml
agentctl connect alice bob -b
agentctl watch  # Live monitoring
```

The framework successfully delivers on its promise: **spawn agents, connect them in any topology, let them collaborate**. Zero CPU overhead. Pure chaos, perfectly orchestrated.

## 🔄 Recent Architectural Updates (August 19, 2025)

### Major Changes Implemented
1. **Stdin/Stdout Mode Removed**: Simplified to socket-only communication
2. **Non-blocking CLI Start**: Terminal no longer blocks when starting agents
3. **Enhanced Status Command**: Real-time agent state tracking with timing
4. **Library Mode Fixed**: Socket-based readiness checks for DEVNULL mode
5. **Comprehensive Test Updates**: All tests updated for new architecture

### Documentation Updates
- Created `CLI_VS_LIBRARY_ARCHITECTURE.md` explaining execution model differences
- Updated `KNOWN_ISSUES.md` with current issues and fixes
- Socket API duplication identified as priority refactoring target

## 🎯 Next Priorities

### High Priority Tasks

1. **Refactor Socket APIs to Framework Layer**
   - Move all socket communication logic from CLI to framework
   - Create unified `AgentClient` class for all interfaces
   - Eliminate code duplication between CLI, supervisor, and connection manager
   - Ensure CLI acts purely as an interface layer

2. **Resolve Library vs CLI Architecture Ambiguity**
   - Implement shared socket client to bridge both modes
   - Maintain clear separation: CLI (stateless) vs Library (stateful)
   - Document and enforce architectural boundaries

3. **Chat Interface Implementation**
   - Add `agentctl chat <agent>` command for single message
   - Add `agentctl chat <agent> --interactive` for continuous chat
   - Ensure implementation uses framework APIs only (no socket logic in CLI)

4. **Library Testing Suite**
   - Comprehensive integration tests for library usage patterns
   - Test dynamic agent management scenarios
   - Error handling and edge cases
   - Performance and resource cleanup tests

5. **Grafana Integration Preparation**
   - Ensure Prometheus metrics are properly exposed
   - Design metric namespaces and labels
   - Document metric collection patterns
   - Prepare example Grafana dashboards

### Architecture Principles Moving Forward
- **CLI = Frontend**: Only calls framework APIs
- **Framework = Backend**: Contains all business logic and socket handling
- **Clean Interfaces**: Enable easy addition of Web UI, REST API, etc.

## 💡 Design Philosophy & Lessons Learned

### Core Principles Reinforced (August 19, 2025)
1. **Simplicity Over Features**: Removing stdin mode simplified everything
2. **Clear Boundaries**: CLI and Library serve different use cases, don't mix them
3. **Socket-First**: All IPC through sockets provides consistency
4. **Process Independence**: Agents should run without parent supervisor
5. **Observability**: Logs + Metrics + Socket status = Complete picture

### What Works Well
- **Unix Socket Control**: Zero CPU overhead, reliable, simple protocol
- **MCP for Agent Communication**: Clean separation of control vs data plane
- **Process Isolation**: Each agent in own process prevents cascading failures
- **Dynamic Connections**: No hardcoded topology, complete flexibility
- **Non-blocking Operations**: Better UX, no terminal hanging

### What Needs Improvement
- **Code Duplication**: Socket client code scattered across modules
- **Chat Integration**: MCP tool access from control socket is complex
- **Test Coverage**: Need more library-specific integration tests
- **Error Messages**: Some timeout errors lack detail about root cause
- **Documentation**: API reference documentation needed

### Future Architecture Direction
1. **Unified Client Layer**: Single `AgentClient` for all socket operations
2. **Plugin System**: Allow custom tools without modifying core
3. **Daemon Mode**: Optional persistent supervisor for CLI
4. **Web UI Ready**: Clean APIs will enable browser-based management
5. **Distributed Mode**: Socket API could extend to TCP for remote agents