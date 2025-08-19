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

## Legacy Stdin Code

### Issue
Stdin-based control code is still present for backward compatibility.

### Impact
- Adds complexity to codebase
- Maintenance burden for legacy path

### Current State
- Socket mode is default and recommended
- Stdin mode available via `--use-stdin` flag
- All new features use socket mode

### Planned
Will be removed after validation period.

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

## Performance Notes

Current performance characteristics:
- **CPU**: < 1% idle (event-driven, no polling)
- **Memory**: ~50MB per agent
- **Latency**: < 10ms for health checks
- **Reliability**: Auto-recovery from crashes

The framework is production-ready with comprehensive error handling and monitoring.