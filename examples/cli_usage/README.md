# CLI Usage Example

This example demonstrates using `agentctl` to manage agents via the command line.

## Files

- `alice.yaml` - Research coordinator agent
- `bob.yaml` - Geography expert agent  
- `charlie.yaml` - History expert agent
- `demo.sh` - Shell script showing CLI commands

## Running the Example

1. Make sure you have API keys set in your `.env` file:
   ```bash
   GOOGLE_API_KEY=your-key-here
   ```

2. Run the demo script:
   ```bash
   ./demo.sh
   ```

## Manual CLI Commands

Start agents:
```bash
agentctl start alice.yaml bob.yaml charlie.yaml
```

Check status:
```bash
agentctl status
```

Connect agents:
```bash
# One-way connection
agentctl connect alice bob

# Bidirectional connection
agentctl connect alice bob -b
```

Stop agents:
```bash
# Stop specific agent
agentctl stop alice

# Stop all agents
agentctl stop --all
```

## Key Features Demonstrated

1. **Zero CPU Usage**: Agents use < 1% CPU when idle (socket mode)
2. **Dynamic Connections**: Connect agents after they're running
3. **Clean Shutdown**: Proper cleanup of all resources
4. **YAML Configuration**: Simple, readable agent configs

## Architecture

Each agent runs as a separate process with:
- MCP server on its configured port (8401, 8402, 8403)
- Control socket at `/tmp/chaotic-af/agent-{name}.sock`
- Connection to configured LLM provider

The socket mode eliminates the CPU spinning issue from stdin polling.
