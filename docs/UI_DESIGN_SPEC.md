# UI Design Specification for Chaotic AF Agent Framework

> **Status**: Ready for implementation
> **Last Updated**: August 19, 2025

## Current System Architecture

### What We Have Built
- Multi-agent framework using MCP (Model Context Protocol)
- Agents communicate via HTTP/JSON-RPC
- Each agent runs as a separate process
- Dynamic connection system via supervisor
- Gemini LLM integration with tool calling

### Key Components
1. **AgentSupervisor**: Manages agent lifecycle
2. **AgentMCPServer**: Each agent's server (FastMCP)
3. **AgentMCPClient**: For agent-to-agent communication
4. **ConnectionManager**: Tracks agent endpoints

### Current Capabilities
- ✅ CLI interface (`agentctl`) for agent management
- ✅ Agent state tracking via ~/.chaotic-af/agents.json
- ✅ Process-based agent isolation
- ✅ Dynamic connection system
- ✅ Structured logging with correlation IDs

### What's Missing
- No real-time visual monitoring
- No web-based interface
- No visual representation of agent topology
- Hard to see message flow visually

## Proposed UI Architecture

### Layer 1: Data Collection (Backend)

```python
# monitoring/collector.py
class AgentEventCollector:
    """Collects events from all agents without interference"""
    
    def __init__(self):
        self.events = []
        self.subscribers = []
        
    async def collect_event(self, event: dict):
        # Store event
        self.events.append(event)
        # Broadcast to UI
        await self.broadcast(event)
```

### Layer 2: API Layer

```python
# monitoring/api.py
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# Enable CORS for React
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/agents")
async def get_agents():
    """Return all registered agents and their status"""
    return {
        "agents": [
            {
                "id": "alpha",
                "status": "running",
                "port": 7001,
                "connections": ["bravo", "charlie"],
                "uptime": "5m 23s",
                "messages_sent": 42,
                "messages_received": 38
            }
        ]
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Real-time event stream"""
    await websocket.accept()
    # Stream events as they happen
```

### Layer 3: Frontend Structure

```
ui/
├── src/
│   ├── components/
│   │   ├── AgentNode.tsx      # Visual representation of agent
│   │   ├── ConnectionLine.tsx  # Shows agent connections
│   │   ├── MessageFlow.tsx     # Animated message visualization
│   │   ├── LogViewer.tsx       # Real-time log display
│   │   └── MetricsPanel.tsx    # CPU, memory, message stats
│   ├── pages/
│   │   ├── Dashboard.tsx       # Main view with all agents
│   │   └── AgentDetail.tsx     # Deep dive into one agent
│   └── services/
│       ├── api.ts              # REST API client
│       └── websocket.ts        # Real-time updates
```

### Layer 4: CLI Integration

The UI should integrate with the existing CLI infrastructure:

```python
# Read agent state from CLI's state file
STATE_FILE = Path.home() / ".chaotic-af" / "agents.json"

# Use CLI commands programmatically
import subprocess

def start_agents_from_ui(config_files):
    result = subprocess.run(
        ["agentctl", "start"] + config_files,
        capture_output=True,
        text=True
    )
    return result.returncode == 0
```

### Layer 5: Integration Points

```python
# How to integrate without breaking existing code:

# 1. Modify AgentLogger to also send to collector
class AgentLogger:
    def __init__(self, agent_id: str, collector_url: str = None):
        self.collector_url = collector_url
        
    def info(self, message: str, **kwargs):
        # Existing logging
        self.logger.info(message, **kwargs)
        
        # New: Send to collector
        if self.collector_url:
            self.send_to_collector({
                "agent_id": self.agent_id,
                "level": "info",
                "message": message,
                "metadata": kwargs
            })

# 2. Update Supervisor to expose agent registry
class AgentSupervisor:
    def get_agent_registry(self):
        return {
            agent_id: {
                "config": config,
                "process": proc,
                "status": self.get_agent_status(agent_id)
            }
            for agent_id, (config, proc) in self.agents.items()
        }
```

## UI Features to Build

### Phase 1: Basic Monitoring
- [ ] Agent status dashboard
- [ ] Real-time log viewer
- [ ] Basic metrics (uptime, message count)

### Phase 2: Interactive Features  
- [ ] Click agent to see details
- [ ] Message flow visualization
- [ ] Connection topology graph
- [ ] Search/filter logs

### Phase 3: Control Features
- [ ] Start/stop agents from UI
- [ ] Create new connections
- [ ] Send test messages
- [ ] Export conversation logs

## Tech Stack Recommendation

### Backend
- **FastAPI**: For REST API and WebSocket
- **Redis**: For event storage (optional)
- **Prometheus**: For metrics (optional)

### Frontend  
- **React**: Component-based UI
- **D3.js** or **React Flow**: For network visualization
- **Material-UI**: For consistent design
- **Socket.io-client**: For WebSocket connection

## Getting Started Commands

```bash
# Backend setup
cd /Users/utkarshsingh/Developer/chaotic-af
mkdir -p monitoring
pip install fastapi uvicorn websockets

# Frontend setup
npx create-react-app agent-ui --template typescript
cd agent-ui
npm install @mui/material d3 reactflow socket.io-client axios
```

## Key Design Principles

1. **Non-Intrusive**: UI should observe, not interfere
2. **Real-Time**: Show events as they happen
3. **Intuitive**: Visual representation of agent relationships  
4. **Performant**: Handle 100+ agents without lag
5. **Decoupled**: UI can be turned off without affecting agents

## API Endpoints Needed

```
GET  /api/agents              # List all agents
GET  /api/agents/{id}         # Get specific agent details
GET  /api/agents/{id}/logs    # Get agent logs
GET  /api/connections         # Get connection topology
GET  /api/messages            # Get recent messages
WS   /ws                      # Real-time event stream
POST /api/agents/{id}/message # Send message to agent (testing)
```

## Event Types to Track

```typescript
interface AgentEvent {
    timestamp: string;
    agent_id: string;
    event_type: 'startup' | 'shutdown' | 'connection' | 'message' | 'error';
    data: any;
}

interface MessageEvent {
    from_agent: string;
    to_agent: string;
    tool_name: string;
    payload: any;
    response: any;
    duration_ms: number;
}
```

This document provides everything needed to build the UI in a new chat session!
