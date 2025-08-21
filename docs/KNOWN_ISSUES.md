# Known Issues

> **Last Updated**: August 21, 2025

## Current Active Issues

### 1. Agent-to-Agent Tool Call Responses Missing in CLI

#### Issue
While agent-to-agent tool calls are visible in interactive CLI (`customer_service → tech_support`), the responses from those tool calls don't appear with the correct directional arrow.

#### Impact
- Users see outgoing messages but not incoming responses
- Creates incomplete view of agent communication flow
- Responses are present in logs but not in CLI display

#### Evidence
```bash
# What users see in CLI:
customer_service → tech_support: How to fix Python errors?
# Missing: customer_service ← tech_support: Here's how to fix it...

# But it's in logs:
[2025-08-21 18:10:44.744] [customer_service] [INFO] Tool response: communicate_with_agent - Success
```

#### Status
Race condition in event subscription or event emission timing. TOOL_CALL_RESPONSE events exist but aren't reaching CLI properly.

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

### 4. CLI Command Module Path Complexity

#### Issue
Users must use full module paths for CLI commands instead of a simple `agentctl` command.

#### Impact
- Poor developer experience with long command names
- `python -m agent_framework.cli.commands start` instead of `agentctl start`
- Makes documentation examples verbose

#### Current State
No CLI script wrapper installed via pip. Users must use full Python module syntax.

## Previously Resolved

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

1. **High**: Agent-to-agent tool call response visibility in CLI
2. **Medium**: Zombie process cleanup automation  
3. **Low**: CLI command wrapper (`agentctl`)
4. **Community**: Windows compatibility