# Known Issues

> **Last Updated**: August 21, 2025

## Current Active Issues

### 1. CLI Command Module Path Complexity

#### Issue
Users must use full module paths for CLI commands instead of a simple `agentctl` command.

#### Impact
- Poor developer experience with long command names
- `python -m agent_framework.cli.commands start` instead of `agentctl start`
- Makes documentation examples verbose

#### Current State
No CLI script wrapper installed via pip. Users must use full Python module syntax.

### 2. Zombie Process Management

#### Issue
When agents crash or are killed unexpectedly, zombie processes can accumulate and interfere with new agent startups.

#### Impact
- `ps aux | grep agent_framework` shows multiple stale processes
- Can cause port conflicts when restarting agents
- May prevent clean shutdown of supervisor processes

#### Workaround
Manually kill processes:
```bash
ps aux | grep -E "agent_framework.network.agent_runner" | grep -v grep | awk '{print $2}' | xargs kill -9
```

#### Root Cause
Process cleanup not always triggered properly during abnormal shutdown scenarios.

### 3. Windows Compatibility

#### Issue
Unix domain sockets are not available on Windows.

#### Impact
- Framework doesn't work on Windows at all
- No alternative IPC mechanism implemented

#### Status
Windows support is not a current priority. Community contributions welcome.

## Previously Resolved

### Agent-to-Agent Response Display (Resolved August 21, 2025)
Interactive CLI was missing agent-to-agent tool call responses. Root cause was data structure mismatch - CLI expected dict payload but MCP client emitted CallToolResult object. Fixed by normalizing event payloads and adding defensive unwrapping.

### High CPU Usage (Resolved)
The original 80-100% CPU usage issue from stdin polling was fixed with Unix socket implementation, achieving < 1% CPU usage.

### CLI Connect Command (Resolved) 
CLI commands now work properly via Unix sockets instead of failing silently.

## Performance Notes

Current performance characteristics:
- **CPU**: < 1% idle (event-driven, no polling)
- **Memory**: ~50MB per agent
- **Latency**: < 10ms for health checks and CLI commands
- **Test Coverage**: 71/71 tests passing

## Priority for Resolution

1. **Medium**: Zombie process cleanup automation  
2. **Low**: CLI command wrapper (`agentctl`)
3. **Community**: Windows compatibility