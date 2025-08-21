# Proposed Socket API Extensions

## Current APIs (Implemented)
- `health` - Check agent status
- `connect` - Connect to another agent
- `shutdown` - Graceful shutdown
- `metrics` - Get metrics (json/prometheus)

## Proposed New APIs

### 1. Connection Management
```python
# Disconnect from another agent
{"cmd": "disconnect", "target": "agent_name"}
Response: {"status": "disconnected"}

# List all connections
{"cmd": "list_connections"}
Response: {"connections": ["alice", "bob"], "endpoints": {...}}
```

### 2. Logging & Debugging
```python
# Get recent logs
{"cmd": "get_logs", "lines": 100, "level": "INFO"}
Response: {"logs": [{"timestamp": "...", "level": "...", "message": "..."}]}

# Get agent configuration
{"cmd": "get_config"}
Response: {"config": {...}}
```

### 3. State Management
```python
# Get conversation history
{"cmd": "get_conversations", "limit": 10}
Response: {"conversations": [...]}

# Clear conversation history
{"cmd": "clear_conversations"}
Response: {"status": "cleared"}
```

### 4. Dynamic Configuration
```python
# Update role prompt
{"cmd": "update_prompt", "prompt": "New role prompt..."}
Response: {"status": "updated"}

# Set log level
{"cmd": "set_log_level", "level": "DEBUG"}
Response: {"status": "updated"}
```

### 5. Tool Management
```python
# List available tools
{"cmd": "list_tools"}
Response: {"tools": ["chat_with_user", "contact_agent", ...]}

# Enable/disable tools
{"cmd": "toggle_tool", "tool": "contact_agent", "enabled": false}
Response: {"status": "updated"}
```

## Implementation Priority
1. **High**: disconnect, list_connections, get_logs (debugging essentials)
2. **Medium**: get_config, get_conversations (state inspection)
3. **Low**: update_prompt, toggle_tool (advanced features)
