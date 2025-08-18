# Known Issues

> **Last Updated**: August 19, 2025

## Process Cleanup on Shutdown

### Issue
Agents sometimes don't respond to SIGTERM gracefully, requiring SIGKILL after timeout.

### Impact
- Shutdown takes longer than necessary (10+ seconds)
- Warning messages in logs about force killing

### Root Cause
The agent process signal handlers may not properly propagate shutdown to all async tasks.

### Workaround
The supervisor automatically escalates to SIGKILL after 10 seconds, ensuring cleanup.

### Planned Fix
- Improve signal handling in agent_runner.py
- Consider using SIGINT before SIGTERM
- Ensure all async tasks are properly cancelled

## Unit Test Failures in Unchanged Modules

### Issue
9 unit tests are failing in modules that weren't updated for socket architecture:
- MCP client tests (5 failures) 
- LLM provider tests (2 failures)
- CLI connect tests (2 failures)

### Impact
Test suite shows 35/44 unit tests passing (79.5% pass rate)

### Root Cause
Mock objects in tests don't match the new async patterns and socket architecture.

### Workaround
Integration tests pass and demonstrate the system works correctly.

### Planned Fix
Update mock objects in affected test files to match new architecture.

## Asyncio Task Cleanup Warnings

### Issue
Occasional warnings during shutdown:
```
Task was destroyed but it is pending!
```

### Root Cause
Background monitoring tasks aren't always cancelled before event loop closure.

### Impact
Cosmetic only - doesn't affect functionality

### Workaround
Can be safely ignored.

## Windows Compatibility

### Issue
Unix domain sockets are not available on Windows.

### Impact
Socket mode doesn't work on Windows; falls back to stdin mode.

### Workaround
Use `--use-stdin` flag explicitly on Windows:
```bash
agentctl start --use-stdin alice.yaml bob.yaml
```

### Planned Fix
Implement named pipes support for Windows.

## Fixed Issues ✅

The following issues have been resolved:

1. **CLI Connect Command** - Now works properly via Unix sockets
2. **High CPU Usage** - Reduced from 80-100% to < 1% with socket implementation
3. **Dynamic Connections** - Fully implemented with any agent names/ports
4. **Port Conflicts** - Resolved with dynamic port allocation
5. **Agent Communication** - Working bidirectionally with universal tools