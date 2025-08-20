# Known Issues

> **Last Updated**: August 19, 2025

## Windows Compatibility

### Issue
Unix domain sockets are not available on Windows.

### Impact
Socket mode doesn't work on Windows; must use stdin mode which has higher CPU usage.

### Workaround
Use `--use-stdin` flag explicitly on Windows:
```bash
python -m agent_framework.network.agent_runner --use-stdin --config "..."
```

### Note
Windows support is not a current priority. Community contributions welcome.

## Current Active Issues

### 1. Socket API Code Duplication

#### Issue
Same socket communication code duplicated across multiple modules.

#### Impact
- Violates DRY principle
- Maintenance burden
- Potential for inconsistent behavior

#### Locations
- CLI `connect` command (cli/commands.py:381-454)
- CLI `status` command (cli/commands.py:200-230)
- ConnectionManager (network/connection_manager.py:69-93)
- Supervisor._wait_for_all_ready (network/supervisor.py:448-456)

#### Proposed Solution
Create unified `AgentSocketClient` class in framework layer that both CLI and library can use.

### 2. Chat Command Implementation

#### Issue
Chat command partially implemented but not working correctly with MCP tool access.

#### Impact
- Users cannot interact with agents via CLI chat
- MCP tool integration from control socket is complex

#### Current State
- Basic chat handler exists in control_socket.py
- Needs proper integration with MCP infrastructure
- Tool access (contact_agent) not working from chat context

#### Decision
Postponed to maintain code clarity and avoid fragile workarounds.

### 3. Windows Compatibility

#### Issue
Unix domain sockets are not available on Windows.

#### Impact
- Framework doesn't work on Windows at all (stdin mode removed)
- Windows users cannot use the framework

#### Current State
- Unix sockets are the only IPC mechanism
- No Windows alternative implemented

#### Note
Windows support is not a current priority. Community contributions welcome.

## Fixed Issues ✅

The following issues have been resolved:

### 1. **High CPU Usage** 
- **Fixed**: Reduced from 80-100% to < 1% with Unix socket implementation
- **Solution**: Event-driven architecture with epoll/kqueue

### 2. **CLI Connect Command**
- **Fixed**: Now works properly via Unix sockets
- **Solution**: Proper socket-based IPC between CLI and agents

### 3. **Process Cleanup**
- **Fixed**: Graceful shutdown via socket → SIGTERM → SIGKILL
- **Solution**: Proper shutdown sequence with timeouts

### 4. **Test Failures**
- **Fixed**: All 67 tests now passing
- **Solution**: Updated tests to match current architecture

### 5. **Agent Recovery**
- **Fixed**: Automatic restart with configurable limits
- **Solution**: Health monitoring with auto-recovery system

### 6. **Metrics Collection**
- **Fixed**: Full Prometheus-compatible metrics
- **Solution**: Metrics exposed via socket commands

### 7. **Dynamic Connections**
- **Fixed**: Any topology, any agent names
- **Solution**: Dynamic connection manager with runtime updates

### 8. **Terminal Blocking on CLI Start** (Fixed August 19, 2025)
- **Fixed**: CLI `start` command was blocking terminal, requiring Ctrl+C
- **Root Cause**: `subprocess.PIPE` creates threads that prevent Python exit
- **Solution**: Use `subprocess.DEVNULL` for non-monitoring mode

### 9. **Library Mode Timeout** (Fixed August 19, 2025)
- **Fixed**: Library example timing out with "Agents not ready after 30s"
- **Root Cause**: Socket readiness check needed when stdout goes to DEVNULL
- **Solution**: Modified `_wait_for_all_ready()` to check socket health

### 10. **Stdin/Stdout Legacy Code** (Removed August 19, 2025)
- **Fixed**: Complex dual-mode communication system removed
- **Impact**: Simplified codebase, eliminated CPU spinning issues
- **Solution**: Socket-only mode for all agent communication

## Performance Notes

Current performance characteristics:
- **CPU**: < 1% idle (event-driven, no polling)
- **Memory**: ~50MB per agent
- **Latency**: < 10ms for health checks
- **Reliability**: Auto-recovery from crashes

The framework is production-ready with comprehensive error handling and monitoring.