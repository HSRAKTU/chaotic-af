# Known Issues

## CLI `connect` Command Non-Functional

### Issue
The `agentctl connect` command doesn't actually work. It prints success but never sends the connection command to agents.

### Impact
Cannot dynamically connect agents via CLI after they're started.

### Workaround
Use the Python API directly:
```python
supervisor = AgentSupervisor()
# ... start agents ...
await supervisor.connect("alice", "bob")  # This works!
```

### Root Cause
The CLI doesn't maintain process stdin handles after starting agents. The supervisor does, which is why demos work.

## High CPU Usage with Multiple Agents

### Issue
When running multiple agents (e.g., examples/simple.py), each agent process consumes 80-100% CPU.

### Root Cause
The agent_runner.py uses blocking `sys.stdin.readline()` in an executor thread, which creates a busy-wait pattern when combined with the async event loop.

### Workaround
- Run fewer agents
- Use shorter demo scripts
- The issue doesn't affect functionality, just performance

### Planned Fix
Replace blocking stdin reads with:
1. Async stdin using `aioconsole` or similar
2. Use select/poll to check stdin availability
3. Or restructure to use a different IPC mechanism (sockets, pipes)

## Asyncio Task Cleanup Warnings

### Issue
When shutting down agents, you may see:
```
Task was destroyed but it is pending!
```

### Root Cause
Background tasks for monitoring agent output aren't properly cancelled before shutdown.

### Impact
Cosmetic only - doesn't affect functionality

### Planned Fix
Properly cancel all tasks in supervisor shutdown sequence.
