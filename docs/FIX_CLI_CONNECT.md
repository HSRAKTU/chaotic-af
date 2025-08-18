# URGENT: Fix CLI Connect Command

The `agentctl connect` command is currently non-functional. It prints success but doesn't actually send commands to agents.

## Current Issue
```python
# In cli/commands.py - THIS DOESN'T WORK
connect_cmd = f"CONNECT:{to_agent}:http://localhost:{to_info['port']}/mcp\n"
# Nothing is sent! Just prints success message
```

## Solution Options

### Option 1: HTTP Admin API
Each agent exposes an admin endpoint:
```python
# In agent_runner.py
@app.post("/admin/connect")
async def add_connection(target: str, endpoint: str):
    await agent.mcp_client.add_connection(target, endpoint)
```

### Option 2: Use Supervisor Process
CLI commands go through a persistent supervisor:
```bash
agentctl daemon start  # Starts supervisor daemon
agentctl connect alice bob  # Daemon handles the connection
```

### Option 3: Store Process Handles
Save stdin file descriptors when starting agents:
```python
state['agents'][name] = {
    'pid': pid,
    'stdin_fd': process.stdin.fileno(),  # Save this
    ...
}
```

## Immediate Action
Add to README known issues:
- `agentctl connect` command not yet implemented
- Use Python API for dynamic connections
