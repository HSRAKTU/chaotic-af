"""Minimal UI Server for Multi-Agent Observability"""

import asyncio
import json
import uuid
from pathlib import Path
from typing import Dict, List
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

from agent_framework.client.socket_client import AgentSocketClient

app = FastAPI(title="Chaotic AF Agent Monitor")

# Store active WebSocket connections
websocket_connections: List[WebSocket] = []

# Agent state cache
agent_states: Dict[str, Dict] = {}

@app.get("/")
async def get_dashboard():
    """Enhanced dashboard with network topology"""
    return HTMLResponse("""
<!DOCTYPE html>
<html>
<head>
    <title>Chaotic AF - Multi-Agent Monitor</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; background: #1a1a1a; color: #fff; }
        .container { display: flex; height: 100vh; }
        .left-panel { width: 60%; padding: 20px; }
        .right-panel { width: 40%; padding: 20px; border-left: 1px solid #333; }
        
        /* Network Topology */
        #topology { 
            width: 100%; 
            height: 400px; 
            border: 1px solid #333; 
            background: #0a0a0a;
            border-radius: 8px;
            margin-bottom: 20px;
            position: relative;
            overflow: hidden;
        }
        
        .agent-node {
            position: absolute;
            width: 120px;
            height: 80px;
            border: 2px solid #333;
            border-radius: 8px;
            background: #2a2a2a;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            font-size: 12px;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .agent-node.running { border-color: #4CAF50; background: #1b2e1b; }
        .agent-node.starting { border-color: #FF9800; background: #2e2e1b; }
        .agent-node.failed { border-color: #F44336; background: #2e1b1b; }
        .agent-node.active { box-shadow: 0 0 20px rgba(76, 175, 80, 0.5); }
        
        .agent-name { font-weight: bold; font-size: 14px; }
        .agent-port { font-size: 10px; color: #888; }
        
        /* Connection Lines */
        .connection-line {
            position: absolute;
            background: #4CAF50;
            height: 2px;
            transform-origin: left center;
            z-index: 1;
            opacity: 0.3;
            transition: all 0.3s ease;
        }
        
        .connection-line.active {
            background: #FFD700;
            height: 4px;
            opacity: 1;
            box-shadow: 0 0 10px #FFD700;
        }
        
        .connection-line.pulse {
            animation: pulse 1s ease-in-out;
        }
        
        @keyframes pulse {
            0% { opacity: 0.3; transform: scaleY(1); }
            50% { opacity: 1; transform: scaleY(2); box-shadow: 0 0 15px #FFD700; }
            100% { opacity: 0.3; transform: scaleY(1); }
        }
        
        /* Animated Message Flow Dots */
        .message-dot {
            position: absolute;
            width: 8px;
            height: 8px;
            background: #FFD700;
            border-radius: 50%;
            z-index: 5;
            box-shadow: 0 0 10px #FFD700;
            animation: flow 2s linear;
        }
        
        @keyframes flow {
            0% { transform: translateX(0) scale(0.5); opacity: 0; }
            10% { opacity: 1; transform: scale(1); }
            90% { opacity: 1; transform: scale(1); }
            100% { transform: translateX(var(--flow-distance)) scale(0.5); opacity: 0; }
        }
        
        .connection-arrow {
            position: absolute;
            width: 0;
            height: 0;
            border-left: 8px solid #4CAF50;
            border-top: 4px solid transparent;
            border-bottom: 4px solid transparent;
            z-index: 2;
            opacity: 0.3;
            transition: all 0.3s ease;
        }
        
        .connection-arrow.active {
            border-left-color: #FFD700;
            opacity: 1;
        }
        
        /* Events Panel */
        .agent-list { 
            display: grid; 
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
            gap: 10px; 
            margin-bottom: 20px;
        }
        
        .agent-card { 
            border: 2px solid #333; 
            padding: 10px; 
            border-radius: 8px;
            background: #2a2a2a;
            font-size: 12px;
        }
        .agent-card.running { border-color: #4CAF50; }
        .agent-card.starting { border-color: #FF9800; }
        .agent-card.failed { border-color: #F44336; }
        
        #events { 
            height: 500px; 
            overflow-y: auto; 
            border: 1px solid #333; 
            padding: 10px; 
            background: #1e1e1e;
            border-radius: 8px;
            font-family: 'Courier New', monospace;
            font-size: 16px;
            line-height: 1.6;
        }
        
        .event { 
            padding: 3px 0; 
            margin: 1px 0;
        }
        .event.outgoing { color: #4CAF50; }
        .event.incoming { color: #2196F3; }
        .event.thinking { color: #FF9800; }
        .arrow-out { color: #4CAF50; font-weight: bold; }
        .arrow-in { color: #2196F3; font-weight: bold; }
        .timestamp { color: #666; font-size: 11px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="left-panel">
            <h1>🌀 Chaotic AF - Multi-Agent Monitor</h1>
            
            <h2>🕸️ Network Topology</h2>
            <div id="topology"></div>
            
            <h2>📊 Agent Status</h2>
            <div id="agents" class="agent-list"></div>
        </div>
        
        <div class="right-panel">
            <h2>💬 Chat Interface</h2>
            <div id="chat-controls" style="margin-bottom: 15px;">
                <select id="agent-select" style="background: #2a2a2a; color: #fff; border: 1px solid #333; padding: 5px; border-radius: 4px; margin-right: 10px;">
                    <option value="">Select Agent...</option>
                </select>
                <br><br>
                <textarea id="message-input" placeholder="Type your message here..." style="width: 100%; height: 60px; background: #2a2a2a; color: #fff; border: 1px solid #333; border-radius: 4px; padding: 10px; resize: vertical; font-family: Arial;"></textarea>
                <br><br>
                <button id="send-btn" onclick="sendMessage()" style="background: #4CAF50; color: #fff; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; margin-right: 10px;">Send Message</button>
                <label style="font-size: 12px;">
                    <input type="checkbox" id="verbose-mode" checked> Verbose Mode
                </label>
            </div>
            
            <h2>📡 Live Event Stream (ALL Agents)</h2>
            <div style="font-size: 12px; color: #888; margin-bottom: 10px;">
                Real-time monitoring of all agent interactions
            </div>
            <div id="events"></div>
        </div>
    </div>
    
    <script>
        const ws = new WebSocket(`ws://${window.location.host}/ws`);
        const agentsDiv = document.getElementById('agents');
        const eventsDiv = document.getElementById('events');
        const topologyDiv = document.getElementById('topology');
        
        let agents = {};
        let agentPositions = {}; // Store agent node positions for animations
        let connections = new Set();
        let activeConnections = new Set(); // Track active message flows
        
        ws.onmessage = function(event) {
            const data = JSON.parse(event.data);
            
            if (data.type === 'agent_status') {
                updateAgentStatus(data.agent_name, data.status);
            } else if (data.type === 'agent_event') {
                displayEvent(data);
                animateConnection(data);
            } else if (data.type === 'chat_response') {
                // Display agent response in event stream
                const eventDiv = document.createElement('div');
                eventDiv.className = 'event incoming';
                eventDiv.innerHTML = `<span class="timestamp">[${new Date().toLocaleTimeString()}]</span> <span class="arrow-in">user ← ${data.agent_name}:</span> ${data.response}`;
                eventsDiv.appendChild(eventDiv);
                eventsDiv.scrollTop = eventsDiv.scrollHeight;
            } else if (data.type === 'chat_error') {
                // Display error
                const eventDiv = document.createElement('div');
                eventDiv.className = 'event';
                eventDiv.style.color = '#F44336';
                eventDiv.innerHTML = `<span class="timestamp">[${new Date().toLocaleTimeString()}]</span> ERROR: ${data.error}`;
                eventsDiv.appendChild(eventDiv);
                eventsDiv.scrollTop = eventsDiv.scrollHeight;
            }
        };
        
        function updateAgentStatus(name, status) {
            agents[name] = status;
            renderAgents();
            renderTopology();
            updateAgentSelect();
        }
        
        function updateAgentSelect() {
            const select = document.getElementById('agent-select');
            const currentValue = select.value;
            
            select.innerHTML = '<option value="">Select Agent...</option>';
            Object.keys(agents).forEach(name => {
                const option = document.createElement('option');
                option.value = name;
                option.textContent = `${name} (${agents[name].status})`;
                if (agents[name].status === 'running') {
                    option.textContent += ' ✓';
                }
                select.appendChild(option);
            });
            
            // Restore selection if still valid
            if (currentValue && agents[currentValue]) {
                select.value = currentValue;
            }
        }
        
        function sendMessage() {
            const agentSelect = document.getElementById('agent-select');
            const messageInput = document.getElementById('message-input');
            const verboseMode = document.getElementById('verbose-mode').checked;
            
            const agentName = agentSelect.value;
            const message = messageInput.value.trim();
            
            if (!agentName) {
                alert('Please select an agent');
                return;
            }
            
            if (!message) {
                alert('Please enter a message');
                return;
            }
            
            // Send chat request to server
            ws.send(JSON.stringify({
                action: 'send_chat',
                agent_name: agentName,
                message: message,
                verbose: verboseMode
            }));
            
            // Add to event stream
            const eventDiv = document.createElement('div');
            eventDiv.className = 'event outgoing';
            eventDiv.innerHTML = `<span class="timestamp">[${new Date().toLocaleTimeString()}]</span> <span class="arrow-out">user → ${agentName}:</span> ${message}`;
            eventsDiv.appendChild(eventDiv);
            eventsDiv.scrollTop = eventsDiv.scrollHeight;
            
            // Clear input
            messageInput.value = '';
        }
        
        function renderAgents() {
            agentsDiv.innerHTML = Object.entries(agents).map(([name, status]) => 
                `<div class="agent-card ${status.status}">
                    <div class="agent-name">${name}</div>
                    <div>Status: ${status.status}</div>
                    <div>Port: ${status.port || 'N/A'}</div>
                    <div>PID: ${status.pid || 'N/A'}</div>
                </div>`
            ).join('');
        }
        
        function renderTopology() {
            const agentNames = Object.keys(agents);
            if (agentNames.length === 0) return;
            
            const centerX = topologyDiv.offsetWidth / 2;
            const centerY = topologyDiv.offsetHeight / 2;
            const radius = Math.min(centerX, centerY) - 80;
            
            topologyDiv.innerHTML = '';
            agentPositions = {}; // Reset positions
            
            // Position agents in a circle and store positions
            agentNames.forEach((name, index) => {
                const angle = (index / agentNames.length) * 2 * Math.PI;
                const x = centerX + radius * Math.cos(angle) - 60;
                const y = centerY + radius * Math.sin(angle) - 40;
                
                // Store position for animations
                agentPositions[name] = { x: x + 60, y: y + 40 };
                
                const node = document.createElement('div');
                node.className = `agent-node ${agents[name].status}`;
                node.id = `agent-${name}`;
                node.style.left = x + 'px';
                node.style.top = y + 'px';
                node.innerHTML = `
                    <div class="agent-name">${name}</div>
                    <div class="agent-port">:${agents[name].port}</div>
                `;
                
                node.onclick = () => highlightAgent(name);
                topologyDiv.appendChild(node);
            });
            
            // Only draw actual connections (will be populated by connection events)
            // Connections will be drawn dynamically when we detect them from agent events
            // This prevents the "all-to-all" visual mess
        }
        
        function drawConnection(fromAgent, toAgent) {
            if (!agentPositions[fromAgent] || !agentPositions[toAgent]) return;
            
            const x1 = agentPositions[fromAgent].x;
            const y1 = agentPositions[fromAgent].y;
            const x2 = agentPositions[toAgent].x;
            const y2 = agentPositions[toAgent].y;
            
            const length = Math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2);
            const angle = Math.atan2(y2 - y1, x2 - x1) * 180 / Math.PI;
            
            // Connection line
            const line = document.createElement('div');
            line.className = 'connection-line';
            line.id = `line-${fromAgent}-${toAgent}`;
            line.style.left = x1 + 'px';
            line.style.top = y1 + 'px';
            line.style.width = length + 'px';
            line.style.transform = `rotate(${angle}deg)`;
            
            // Arrow for bidirectional
            const arrow = document.createElement('div');
            arrow.className = 'connection-arrow';
            arrow.id = `arrow-${fromAgent}-${toAgent}`;
            arrow.style.left = (x1 + x2) / 2 + 'px';
            arrow.style.top = (y1 + y2) / 2 + 'px';
            arrow.style.transform = `rotate(${angle}deg)`;
            
            topologyDiv.appendChild(line);
            topologyDiv.appendChild(arrow);
        }
        
        function animateConnection(eventData) {
            // Animate connections during tool calls
            if (eventData.event_type === 'tool_call_making') {
                const tool = eventData.data.tool || '';
                if (tool.startsWith('communicate_with_')) {
                    const target = eventData.data.target;
                    const from = eventData.agent_id;
                    
                    // Ensure connection line exists (draw it if not already drawn)
                    ensureConnectionExists(from, target);
                    
                    // Animate message flow from sender to receiver
                    createFlowingDot(from, target);
                    highlightConnection(from, target);
                    pulseAgent(from, '#4CAF50'); // Green for sending
                }
            } else if (eventData.event_type === 'tool_call_response') {
                const tool = eventData.data.tool || '';
                if (tool.startsWith('communicate_with_')) {
                    const target = eventData.data.target;
                    const from = eventData.agent_id;
                    
                    // Animate response flow back
                    const responseAgent = eventData.data.response?.agent || target;
                    ensureConnectionExists(responseAgent, from);
                    createFlowingDot(responseAgent, from);
                    highlightConnection(responseAgent, from);
                    pulseAgent(from, '#2196F3'); // Blue for receiving
                }
            }
        }
        
        function ensureConnectionExists(fromAgent, toAgent) {
            // Only draw connection if it doesn't already exist
            const lineId = `line-${fromAgent}-${toAgent}`;
            if (!document.getElementById(lineId)) {
                drawConnection(fromAgent, toAgent);
            }
        }
        
        function createFlowingDot(fromAgent, toAgent) {
            if (!agentPositions[fromAgent] || !agentPositions[toAgent]) return;
            
            const x1 = agentPositions[fromAgent].x;
            const y1 = agentPositions[fromAgent].y;
            const x2 = agentPositions[toAgent].x;
            const y2 = agentPositions[toAgent].y;
            
            const dot = document.createElement('div');
            dot.className = 'message-dot';
            dot.style.left = x1 + 'px';
            dot.style.top = y1 + 'px';
            dot.style.setProperty('--flow-distance', `${Math.sqrt((x2-x1)**2 + (y2-y1)**2)}px`);
            
            const angle = Math.atan2(y2 - y1, x2 - x1) * 180 / Math.PI;
            dot.style.transform = `rotate(${angle}deg)`;
            
            topologyDiv.appendChild(dot);
            
            // Remove dot after animation
            setTimeout(() => {
                if (dot.parentNode) {
                    topologyDiv.removeChild(dot);
                }
            }, 2000);
        }
        
        function highlightConnection(from, to) {
            // Highlight the connection line
            const lineId = `line-${from}-${to}`;
            const arrowId = `arrow-${from}-${to}`;
            
            const line = document.getElementById(lineId);
            const arrow = document.getElementById(arrowId);
            
            if (line) {
                line.classList.add('active');
                line.classList.add('pulse');
                setTimeout(() => {
                    line.classList.remove('active', 'pulse');
                }, 1500);
            }
            
            if (arrow) {
                arrow.classList.add('active');
                setTimeout(() => {
                    arrow.classList.remove('active');
                }, 1500);
            }
        }
        
        function pulseAgent(agentName, color) {
            const agent = document.getElementById(`agent-${agentName}`);
            if (agent) {
                agent.style.boxShadow = `0 0 20px ${color}`;
                agent.classList.add('active');
                setTimeout(() => {
                    agent.style.boxShadow = '';
                    agent.classList.remove('active');
                }, 1000);
            }
        }
        
        function highlightAgent(name) {
            // Highlight agent node
            document.querySelectorAll('.agent-node').forEach(node => {
                node.classList.remove('active');
            });
            const targetAgent = document.getElementById(`agent-${name}`);
            if (targetAgent) {
                targetAgent.classList.add('active');
                setTimeout(() => targetAgent.classList.remove('active'), 2000);
            }
        }
        
        function displayEvent(event) {
            const eventType = event.event_type;
            const agentId = event.agent_id;
            const data = event.data;
            const timestamp = new Date().toLocaleTimeString();
            
            let message = '';
            let className = '';
            
            if (eventType === 'tool_call_making') {
                const tool = data.tool || '';
                if (tool.startsWith('communicate_with_')) {
                    const target = data.target || '';
                    const payload = data.payload || {};
                    const msg = (payload.message || '').substring(0, 50) + '...';
                    message = `<span class="arrow-out">${agentId} → ${target}:</span> ${msg}`;
                    className = 'outgoing';
                } else {
                    message = `<span style="color: #FF9800">[${agentId} thinking...]</span>`;
                    className = 'thinking';
                }
            } else if (eventType === 'tool_call_response') {
                const tool = data.tool || '';
                if (tool.startsWith('communicate_with_')) {
                    const target = data.target || '';
                    const response = data.response || {};
                    const msg = (response.response || '').substring(0, 50) + '...';
                    const fromAgent = response.agent || target;
                    message = `<span class="arrow-in">${agentId} ← ${fromAgent}:</span> ${msg}`;
                    className = 'incoming';
                }
            } else if (eventType === 'tool_call_received') {
                message = `<span style="color: #9C27B0">[${agentId}] Tool call received</span>`;
                className = 'received';
            }
            
            if (message) {
                const eventDiv = document.createElement('div');
                eventDiv.className = `event ${className}`;
                eventDiv.innerHTML = `<span class="timestamp">[${timestamp}]</span> ${message}`;
                eventsDiv.appendChild(eventDiv);
                eventsDiv.scrollTop = eventsDiv.scrollHeight;
                
                // Keep only last 100 events for performance
                while (eventsDiv.children.length > 100) {
                    eventsDiv.removeChild(eventsDiv.firstChild);
                }
            }
        }
        
        // Request initial agent status
        ws.onopen = function() {
            console.log('Connected to Chaotic AF Monitor');
        };
        
        ws.onerror = function(error) {
            console.log('WebSocket error:', error);
        };
        
        ws.onclose = function() {
            console.log('Disconnected from monitor');
            setTimeout(() => location.reload(), 3000);
        };
        
        // Auto-refresh every 10 seconds
        setInterval(() => {
            if (ws.readyState === WebSocket.OPEN) {
                ws.send(JSON.stringify({action: 'refresh'}));
            }
        }, 10000);
        
        // Add Enter key support for chat
        document.getElementById('message-input').addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        // Preset chaos messages for quick testing
        window.triggerChaosTest = function() {
            const select = document.getElementById('agent-select');
            const input = document.getElementById('message-input');
            
            if (select.value) {
                input.value = 'CHAOS DRILL: Pass this message to ALL other agents in sequence. Each agent should contact the next agent. Create a full discussion chain!';
                sendMessage();
            } else {
                alert('Select an agent first');
            }
        };
        
        // Add chaos button
        setTimeout(() => {
            const chatControls = document.getElementById('chat-controls');
            const chaosBtn = document.createElement('button');
            chaosBtn.innerHTML = '🌪️ Trigger Chaos Test';
            chaosBtn.style.cssText = 'background: #F44336; color: #fff; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; margin-left: 10px;';
            chaosBtn.onclick = window.triggerChaosTest;
            chatControls.appendChild(chaosBtn);
        }, 1000);
    </script>
</body>
</html>
    """)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket for real-time agent monitoring and chat"""
    await websocket.accept()
    websocket_connections.append(websocket)
    
    try:
        # Send current agent status
        agent_status = await get_all_agent_status()
        for name, status in agent_status.items():
            await websocket.send_text(json.dumps({
                "type": "agent_status",
                "agent_name": name,
                "status": status
            }))
        
        # Handle WebSocket messages and monitor events simultaneously
        import asyncio
        from agent_framework.mcp.client import AgentMCPClient
        from agent_framework.core.events import EventStream
        from agent_framework.core.logging import AgentLogger
        
        async def handle_websocket_messages():
            """Handle chat requests from UI"""
            try:
                while True:
                    message = await websocket.receive_text()
                    data = json.loads(message)
                    
                    if data.get('action') == 'send_chat':
                        agent_name = data.get('agent_name')
                        message_text = data.get('message')
                        verbose = data.get('verbose', True)
                        
                        # Send chat via MCP
                        try:
                            client = AgentMCPClient(
                                agent_id="ui-user",
                                event_stream=EventStream("ui-user"),
                                logger=AgentLogger("ui-user", "ERROR")
                            )
                            
                            # Connect to agent
                            agent_info = agent_status.get(agent_name)
                            if agent_info:
                                await client.add_connection(
                                    agent_name, 
                                    f"http://localhost:{agent_info['port']}/mcp"
                                )
                                
                                # Send message
                                response = await client.call_tool(
                                    server_name=agent_name,
                                    tool_name="chat_with_user",
                                    arguments={"message": message_text, "conversation_id": str(uuid.uuid4())}
                                )
                                
                                # Send response back to UI
                                await websocket.send_text(json.dumps({
                                    "type": "chat_response",
                                    "agent_name": agent_name,
                                    "response": response.data.get('response', str(response))
                                }))
                                
                                await client.close_all()
                        except Exception as e:
                            await websocket.send_text(json.dumps({
                                "type": "chat_error",
                                "error": str(e)
                            }))
            except:
                pass  # WebSocket closed
        
        # Start both message handling and agent monitoring
        await asyncio.gather(
            handle_websocket_messages(),
            subscribe_to_all_agents(websocket),
            return_exceptions=True
        )
        
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        if websocket in websocket_connections:
            websocket_connections.remove(websocket)

async def get_all_agent_status():
    """Get status of all agents"""
    # Read agent state file
    state_file = Path.home() / ".chaotic-af" / "agents.json"
    if not state_file.exists():
        return {}
    
    with open(state_file) as f:
        state = json.load(f)
    
    # Get health status for each agent
    agent_status = {}
    for name, info in state.get('agents', {}).items():
        try:
            health = await AgentSocketClient.health_check(name, timeout=1.0)
            agent_status[name] = {
                "status": "running" if health.get('status') == 'ready' else "starting",
                "port": info.get('port'),
                "pid": info.get('pid'),
                "connections": []  # Could get from agent if needed
            }
        except:
            agent_status[name] = {
                "status": "failed",
                "port": info.get('port'),
                "pid": info.get('pid'),
                "connections": []
            }
    
    return agent_status

async def subscribe_to_all_agents(websocket: WebSocket):
    """Subscribe to events from ALL running agents simultaneously"""
    state_file = Path.home() / ".chaotic-af" / "agents.json"
    if not state_file.exists():
        print("No agent state file found")
        return
    
    with open(state_file) as f:
        state = json.load(f)
    
    print(f"🌐 UI: Subscribing to {len(state.get('agents', {}))} agents...")
    
    async def handle_event(event, agent_name):
        """Forward agent events to WebSocket with enhanced data"""
        try:
            event_data = {
                "type": "agent_event",
                "agent_name": agent_name,
                "event_type": event.get('type'),
                "agent_id": event.get('agent_id'),
                "data": event.get('data'),
                "timestamp": event.get('timestamp')
            }
            await websocket.send_text(json.dumps(event_data))
            
            # Debug log for complex interactions
            event_type = event.get('type')
            if event_type in ['tool_call_making', 'tool_call_response']:
                tool = event.get('data', {}).get('tool', '')
                if tool.startswith('communicate_with_'):
                    print(f"🔥 UI: {agent_name} {event_type} for {tool}")
                    
        except Exception as e:
            print(f"WebSocket send error: {e}")
    
    # Subscribe to each agent with error handling
    tasks = []
    successful_subscriptions = 0
    
    for agent_name in state.get('agents', {}):
        try:
            print(f"📡 Subscribing to {agent_name}...")
            task = await AgentSocketClient.subscribe_events(
                agent_name, 
                lambda event, name=agent_name: asyncio.create_task(handle_event(event, name))
            )
            tasks.append((agent_name, task))
            successful_subscriptions += 1
            print(f"✅ Subscribed to {agent_name}")
        except Exception as e:
            print(f"❌ Failed to subscribe to {agent_name}: {e}")
    
    print(f"🎯 UI: Successfully subscribed to {successful_subscriptions} agents")
    print("🌪️ CHAOS MODE: All agent interactions will be visible!")
    
    # Keep connections alive - DO NOT CLOSE THEM
    print("🌐 UI: Event monitoring active - keeping connections alive...")
    
    # Create a never-ending task to keep subscriptions active
    try:
        while True:
            # Just sleep and keep monitoring - DON'T try to read from WebSocket here
            # The WebSocket reading happens in handle_websocket_messages()
            await asyncio.sleep(10)
            # Optionally refresh agent status periodically
            print(f"📊 UI: Monitoring {len(tasks)} agents...")
    except asyncio.CancelledError:
        print("🔌 UI: Monitoring cancelled")
    except Exception as e:
        print(f"WebSocket monitoring error: {e}")
    finally:
        # Cancel all subscriptions when WebSocket closes
        print("🔌 Closing UI subscriptions...")
        for agent_name, task in tasks:
            if not task.done():
                task.cancel()
                print(f"🚫 Cancelled subscription to {agent_name}")

@app.get("/api/agents")
async def list_agents():
    """REST API for agent list"""
    return await get_all_agent_status()

if __name__ == "__main__":
    print("🌀 Starting Chaotic AF Multi-Agent Monitor...")
    print("📱 Open: http://localhost:8080")
    print("👀 This will show ALL agent interactions simultaneously!")
    uvicorn.run(app, host="0.0.0.0", port=8080)
