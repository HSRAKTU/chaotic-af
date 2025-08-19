"""Core Agent implementation that combines all components.

Requirements:
- Integrate LLM, MCP server, MCP clients
- Handle tool calls from LLM responses
- Maintain agent state and conversations
- Support both agent and user interactions
- Full observability through logging and events
"""

import asyncio
from typing import Dict, Any, List, Optional
import uuid

from ..core.config import AgentConfig, get_llm_key
from ..core.events import EventStream, EventType
from ..core.logging import AgentLogger
from ..core.llm import create_llm_provider, ToolCall
from ..mcp.server_universal import UniversalAgentMCPServer
from ..mcp.client import AgentMCPClient
from ..core.metrics import MetricsCollector, AgentMetrics


class Agent:
    """A single agent node with LLM, MCP server, and MCP client capabilities.
    
    This is the core abstraction that brings together:
    - LLM for reasoning and responses
    - MCP Server for receiving communications
    - MCP Clients for reaching out to other agents/tools
    - Event streaming for observability
    - Structured logging
    """
    
    def __init__(self, config: AgentConfig, available_agents: List[str]):
        self.config = config
        self.agent_id = config.name
        self.available_agents = available_agents
        
        # Initialize event stream
        self.event_stream = EventStream(self.agent_id)
        
        # Initialize logger
        self.logger = AgentLogger(
            agent_id=self.agent_id,
            log_level=config.log_level,
            log_file=config.log_file
        )
        
        # Initialize LLM
        api_key = get_llm_key(config.llm_provider)
        self.llm = create_llm_provider(
            provider=config.llm_provider,
            api_key=api_key,
            model=config.llm_model
        )
        
        # Initialize MCP Client for outgoing connections
        self.mcp_client = AgentMCPClient(
            agent_id=self.agent_id,
            event_stream=self.event_stream,
            logger=self.logger
        )
        
        # Initialize Universal MCP Server for incoming connections
        self.mcp_server = UniversalAgentMCPServer(
            agent_id=self.agent_id,
            agent_role=config.role_prompt,
            llm_provider=self.llm,
            event_stream=self.event_stream,
            logger=self.logger,
            mcp_client=self.mcp_client
        )
        
        # Initialize metrics
        self.metrics_collector = MetricsCollector()
        self.metrics = AgentMetrics(self.metrics_collector)
        
        # Track if agent is running
        self.is_running = False
        self._server_task: Optional[asyncio.Task] = None
    
    async def start(self):
        """Start the agent - but don't connect to others yet."""
        if self.is_running:
            self.logger.warning("Agent already running")
            return
        
        self.logger.info(f"Starting agent {self.agent_id}")
        
        try:
            # Start MCP server in background
            self._server_task = asyncio.create_task(
                self.mcp_server.run(port=self.config.port)
            )
            
            self.is_running = True
            self.logger.info(f"Agent {self.agent_id} started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start agent: {str(e)}")
            raise
    
    async def connect_to_peers(self):
        """Connect to external MCP servers only. Agent connections are now dynamic."""
        self.logger.info(f"Agent {self.agent_id} ready for dynamic connections")
        
        # Only connect to external MCP servers configured in YAML
        for server in self.config.external_mcp_servers:
            try:
                await self.mcp_client.add_connection(
                    server["name"],
                    server["url"]
                )
                self.logger.info(f"Connected to external server: {server['name']}")
            except Exception as e:
                self.logger.error(
                    f"Failed to connect to external server {server['name']}: {str(e)}",
                    event_type="connection",
                    correlation_id=None
                )
        
        # Update server's available connections
        if hasattr(self.mcp_server, 'update_connections'):
            current_connections = list(self.mcp_client.connections.keys())
            self.mcp_server.update_connections(current_connections)
    

    
    async def handle_tool_calls(self, tool_calls: List[ToolCall]) -> List[Dict[str, Any]]:
        """Execute tool calls requested by the LLM.
        
        This is where LLM tool calls get translated into actual MCP calls.
        """
        results = []
        
        for tool_call in tool_calls:
            correlation_id = str(uuid.uuid4())
            
            # Check if this is an agent communication tool
            if tool_call.tool.startswith("contact_"):
                # Extract agent name
                target_agent = tool_call.tool.replace("contact_", "")
                message = tool_call.parameters.get("message", "")
                
                # Use MCP client to communicate
                result = await self.mcp_client.communicate_with_agent(
                    target_agent=target_agent,
                    message=message
                )
                
                results.append({
                    "tool_call_id": tool_call.id,
                    "result": result
                })
            
            else:
                # This is an external tool call
                # Parse server.tool format
                if "." in tool_call.tool:
                    server_name, tool_name = tool_call.tool.split(".", 1)
                    
                    result = await self.mcp_client.call_tool(
                        server_name=server_name,
                        tool_name=tool_name,
                        arguments=tool_call.parameters
                    )
                    
                    results.append({
                        "tool_call_id": tool_call.id,
                        "result": result
                    })
                else:
                    # Unknown tool format
                    self.logger.warning(f"Unknown tool format: {tool_call.tool}")
                    results.append({
                        "tool_call_id": tool_call.id,
                        "result": {"error": f"Unknown tool: {tool_call.tool}"}
                    })
        
        return results
    
    async def think_and_act(
        self,
        prompt: str,
        context: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """Have the agent think about a prompt and take action if needed.
        
        This is used for proactive agent behavior, not responses to other agents.
        """
        correlation_id = str(uuid.uuid4())
        
        self.logger.info(f"Agent thinking about: {prompt[:100]}...")
        
        # Build messages
        messages = context or []
        messages.append({"role": "user", "content": prompt})
        
        # Add system message if not present
        if not any(m["role"] == "system" for m in messages):
            messages.insert(0, {
                "role": "system",
                "content": self.mcp_server._build_agent_system_prompt()
            })
        
        # Get LLM response with tools
        tools = self.mcp_server._get_agent_tools()
        response = await self.llm.complete(messages, tools)
        
        # Log reasoning
        if response.reasoning:
            self.logger.log_llm_reasoning(response.reasoning, correlation_id)
        
        # Handle tool calls
        if response.tool_calls:
            self.logger.info(f"Agent wants to use tools: {[tc.tool for tc in response.tool_calls]}")
            
            # Execute tool calls
            tool_results = await self.handle_tool_calls(response.tool_calls)
            
            # Add tool results to messages
            messages.append({"role": "assistant", "content": response.content})
            
            for result in tool_results:
                messages.append({
                    "role": "tool",
                    "content": f"Tool result: {result['result']}"
                })
            
            # Get final response after tool use
            final_response = await self.llm.complete(messages)
            return final_response.content
        
        return response.content
    
    async def stop(self):
        """Stop the agent gracefully."""
        if not self.is_running:
            return
        
        self.logger.info(f"Stopping agent {self.agent_id}")
        
        try:
            # Close all client connections
            await self.mcp_client.close_all()
            
            # Cancel server task
            if self._server_task:
                self._server_task.cancel()
                try:
                    await self._server_task
                except asyncio.CancelledError:
                    pass
            
            self.is_running = False
            
            # Emit stopped event
            await self.event_stream.emit(
                EventType.AGENT_STOPPED,
                {"agent_id": self.agent_id}
            )
            
            self.logger.info(f"Agent {self.agent_id} stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping agent: {str(e)}")
    
    def subscribe_to_events(self, callback):
        """Subscribe to agent events for monitoring."""
        return self.event_stream.subscribe(callback)
