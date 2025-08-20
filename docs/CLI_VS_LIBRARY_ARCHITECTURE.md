# CLI vs Library Architecture: Understanding the Fundamental Differences

## Overview

This document explains the critical architectural differences between CLI and Library usage in the Chaotic AF framework. Understanding these differences is essential for making informed design decisions about socket APIs, supervisor methods, and code organization.

## The Key Architectural Difference

### 1. Library Usage (Python Script)

When using Chaotic AF as a Python library, your application has a **long-running process** that maintains the supervisor instance:

```python
# Your Python script is LONG-RUNNING
supervisor = AgentSupervisor()  # Supervisor lives in YOUR process
supervisor.add_agent(alice)
await supervisor.start_all()    # Agents are child processes
await supervisor.connect(...)   # Supervisor can directly manage its children
# ... supervisor stays alive throughout your application ...
await supervisor.stop_all()     # Supervisor can cleanly shut down its children
```

**Key characteristics:**
- Single, persistent process
- Supervisor instance remains in memory
- Direct parent-child relationship with agent processes
- Can use internal methods and state
- Full lifecycle control

### 2. CLI Usage (Terminal Commands)

When using the CLI, each command is a **separate, short-lived process**:

```bash
# Each command is SEPARATE and SHORT-LIVED
$ agentctl start alice.yaml     # Creates supervisor, starts agent, EXITS
# [Supervisor process is GONE, but agent processes keep running]

$ agentctl connect alice bob    # NEW process - no supervisor instance!
# Must use sockets to talk to the already-running agents

$ agentctl status              # Another NEW process - no supervisor!
# Again, must use sockets to check on agents
```

**Key characteristics:**
- Multiple, independent processes
- No persistent supervisor
- Agents run as orphaned processes
- Must use IPC (sockets) for all communication
- Stateless commands

## Visual Representation

### Library Mode:
```
┌─────────────────────────────────────┐
│   Your Python Application           │
│   (Long-running process)            │
│                                     │
│   ┌─────────────────────────┐      │
│   │   AgentSupervisor       │      │
│   │   - Manages lifecycle   │      │
│   │   - Holds references    │      │
│   │   - Direct control      │      │
│   └────────┬───────┬────────┘      │
│            │       │                │
└────────────┼───────┼────────────────┘
             │       │
      ┌──────▼──┐ ┌──▼──────┐
      │ Agent   │ │ Agent   │
      │ Process │ │ Process │
      │ (alice) │ │ (bob)   │
      └─────────┘ └─────────┘
```

### CLI Mode:
```
$ agentctl start alice.yaml
┌─────────────────────┐
│ CLI Process #1      │
│ - Creates supervisor│
│ - Starts agent      │
│ - EXITS            │
└─────────────────────┘
         │
         ▼
    ┌─────────┐
    │ Agent   │
    │ Process │
    │ (alice) │ ← Running independently
    └────┬────┘
         │
         ▼ Socket API
         
$ agentctl connect alice bob
┌─────────────────────┐
│ CLI Process #2      │
│ - No supervisor!    │
│ - Uses socket API   │
│ - EXITS            │
└─────────────────────┘
```

## Why This Architecture Makes Sense

### 1. **Agent Independence**
Agents are designed to run independently without requiring a parent supervisor. This enables:
- Resilience: Supervisor crash doesn't kill agents
- Flexibility: Agents can be managed by different tools
- Distributed: Agents could potentially run on different machines

### 2. **CLI Statelessness**
Each CLI command being independent provides:
- Simplicity: No daemon process to manage
- Reliability: No persistent state to corrupt
- Unix philosophy: Do one thing well and exit

### 3. **Socket API as Universal Interface**
The socket API serves as a common communication layer:
- Works for both supervised and orphaned agents
- Enables tool interoperability
- Provides a stable interface regardless of how agent was started

## Current Implementation Issues

### The Duplication Problem

Currently, we have socket communication code duplicated in multiple places:

1. **CLI connect command** (`cli/commands.py`): Direct socket implementation
2. **CLI status command** (`cli/commands.py`): Another socket implementation  
3. **ConnectionManager** (`network/connection_manager.py`): Same socket logic
4. **Supervisor's _wait_for_all_ready** (`network/supervisor.py`): Socket health checks

This violates DRY (Don't Repeat Yourself) principle.

### Why The Duplication Exists

- CLI commands can't use supervisor methods (no supervisor instance)
- Each component independently implemented socket communication
- No shared abstraction layer was created

## Proposed Solution: Shared Socket Client

Create a unified socket client that both CLI and library can use:

```python
# agent_framework/network/agent_socket_client.py
class AgentSocketClient:
    """Unified client for agent socket communication."""
    
    @staticmethod
    async def send_command(agent_name: str, command: dict) -> dict:
        """Send command to agent via socket."""
        # Single implementation used everywhere
    
    @staticmethod
    async def health_check(agent_name: str) -> bool:
        """Check if agent is healthy."""
        # Reusable health check
    
    @staticmethod
    async def connect_agents(from_agent: str, to_agent: str, to_port: int) -> bool:
        """Connect one agent to another."""
        # Shared connection logic
```

### Benefits:
1. **Single source of truth** for socket communication
2. **Consistent behavior** across CLI and library
3. **Easier maintenance** - fix bugs in one place
4. **Better testing** - test the client once

### Usage:

**In CLI commands:**
```python
# cli/commands.py
async def connect_command():
    success = await AgentSocketClient.connect_agents(
        "alice", "bob", 8002
    )
```

**In Supervisor/ConnectionManager:**
```python
# network/connection_manager.py
async def connect_agents(self, from_agent, to_agent):
    port = self.agent_registry[to_agent]
    return await AgentSocketClient.connect_agents(
        from_agent, to_agent, port
    )
```

## Design Principles

### 1. **Separation of Concerns**
- **Supervisor**: Manages process lifecycle for library users
- **Socket API**: Provides communication for all users
- **CLI**: Provides stateless commands using socket API
- **Library**: Provides stateful management via supervisor

### 2. **Progressive Enhancement**
- Basic: Use CLI for simple agent management
- Advanced: Use library for complex orchestration
- Both use the same underlying agents and socket API

### 3. **No Assumptions**
- Don't assume supervisor exists (CLI mode)
- Don't assume agents were started by current process
- Don't assume specific startup method

## Decision Matrix

| Feature | Library Mode | CLI Mode | Shared Component |
|---------|--------------|----------|------------------|
| Start agents | `supervisor.start_all()` | `agentctl start` | Agent process |
| Stop agents | `supervisor.stop_all()` | `agentctl stop` | Socket shutdown command |
| Connect agents | `supervisor.connect()` | `agentctl connect` | AgentSocketClient |
| Check health | `supervisor.get_health()` | `agentctl health` | AgentSocketClient |
| View status | `supervisor.get_status()` | `agentctl status` | AgentSocketClient |
| Agent persistence | Until supervisor stops | Until explicitly stopped | Independent processes |

## Common Misconceptions

### ❌ "CLI and library should use the same supervisor methods"
**Reality**: CLI has no supervisor instance to call methods on.

### ❌ "We're duplicating code unnecessarily"  
**Reality**: We're duplicating code unnecessarily! But the solution is a shared socket client, not shared supervisor methods.

### ❌ "Library mode is better than CLI"
**Reality**: They serve different purposes. Library for integration, CLI for operations.

## Future Considerations

### 1. **Daemon Mode**
We could add a supervisor daemon that CLI commands communicate with:
```bash
$ agentctl daemon start  # Long-running supervisor
$ agentctl start alice   # Talks to daemon
```

### 2. **Remote Agents**
Socket API could be extended to TCP for remote agents:
```python
await AgentSocketClient.connect_remote(
    "alice", "remote-bob", "192.168.1.100:8002"
)
```

### 3. **State Persistence**
Current JSON file could be replaced with more robust state management:
- SQLite for local state
- Redis for distributed state
- etcd for cluster coordination

## Summary

The architectural difference between CLI and Library usage is fundamental and intentional:

- **Library**: Stateful, long-running, direct control via supervisor
- **CLI**: Stateless, short-lived, indirect control via sockets
- **Socket API**: Universal communication layer for both

The key insight is that we need a shared socket client implementation, not shared supervisor methods. This respects the architectural boundaries while eliminating code duplication.

## References

- [Unix Philosophy](https://en.wikipedia.org/wiki/Unix_philosophy): Do one thing well
- [Don't Repeat Yourself](https://en.wikipedia.org/wiki/Don%27t_repeat_yourself): DRY principle
- [Inter-Process Communication](https://en.wikipedia.org/wiki/Inter-process_communication): IPC patterns

---
*Document created: 2025-08-19*  
*Last updated: 2025-08-19*
