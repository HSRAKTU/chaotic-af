"""Universal Agent MCP Server - uses a single contact_agent tool.

This approach works with current FastMCP without needing dynamic tool registration.
"""

import uuid
from typing import Dict, Any, Optional, List, TYPE_CHECKING
from datetime import datetime, timezone

from fastmcp import FastMCP, Context
from ..core.events import EventStream, EventType
from ..core.logging import AgentLogger
from ..core.llm import LLMProvider, ToolDefinition, ToolCall

if TYPE_CHECKING:
    from .client import AgentMCPClient


class UniversalAgentMCPServer:
    """MCP Server with universal contact_agent tool."""
    
    def __init__(
        self,
        agent_id: str,
        agent_role: str,
        llm_provider: LLMProvider,
        event_stream: EventStream,
        logger: AgentLogger,
        mcp_client: Optional['AgentMCPClient'] = None
    ):
        self.agent_id = agent_id
        self.agent_role = agent_role
        self.llm = llm_provider
        self.event_stream = event_stream
        self.logger = logger
        self.mcp_client = mcp_client
        
        # Track available connections dynamically
        self.available_connections: List[str] = []
        
        # Create FastMCP server
        self.server = FastMCP()
        
        # Register universal tools
        self._register_tools()
    
    def _build_agent_system_prompt(self) -> str:
        """Build system prompt with dynamic connections."""
        available_agents = ", ".join(self.available_connections) if self.available_connections else "None"
        
        return f"""You are Agent {self.agent_id}, part of a multi-agent AI system.

Your specialized role: {self.agent_role}

You are connected to these agents: {available_agents}

IMPORTANT: To communicate with another agent, you MUST use the contact_agent tool (not communicate_with_agent).
Example: contact_agent(agent_name="alice", message="Hello Alice!")

The contact_agent tool is YOUR tool for reaching out to other agents.
Do NOT use communicate_with_agent - that's for receiving messages from others.

Remember: You are part of a collaborative system. Be helpful, share information, 
and coordinate effectively with other agents."""
    
    def update_connections(self, connections: List[str]):
        """Update the list of available connections."""
        self.available_connections = connections
        self.logger.info(f"Updated connections: {connections}")
    
    def _register_tools(self):
        """Register universal agent communication tools."""
        
        @self.server.tool
        async def health_check(ctx: Context) -> Dict[str, str]:
            """Simple health check endpoint."""
            return {
                "status": "healthy",
                "agent": self.agent_id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        @self.server.tool
        async def contact_agent(
            ctx: Context,
            agent_name: str,
            message: str,
            conversation_id: Optional[str] = None
        ) -> Dict[str, Any]:
            """Universal tool to contact any connected agent.
            
            Args:
                agent_name: Name of the agent to contact
                message: Message to send
                conversation_id: Optional conversation ID for threading
            """
            correlation_id = str(uuid.uuid4())
            
            # Check if we're connected to this agent
            if agent_name not in self.available_connections:
                return {
                    "error": f"Not connected to agent '{agent_name}'",
                    "available_agents": self.available_connections
                }
            
            # Use MCP client to communicate
            if not self.mcp_client:
                return {
                    "error": "MCP client not available",
                    "details": "Cannot execute tool calls without MCP client"
                }
            
            try:
                # Log outgoing communication
                self.logger.log_tool_call_making(
                    tool_name="communicate_with_agent",
                    to_target=agent_name,
                    payload={
                        "from_agent": self.agent_id,
                        "message": message,
                        "conversation_id": conversation_id
                    },
                    correlation_id=correlation_id
                )
                
                # Make the call
                result = await self.mcp_client.communicate_with_agent(
                    target_agent=agent_name,
                    message=message,
                    conversation_id=conversation_id
                )
                
                # Log response
                self.logger.log_tool_response(
                    tool_name="communicate_with_agent",
                    response=result,
                    success=True,
                    correlation_id=correlation_id
                )
                
                return result
                
            except Exception as e:
                self.logger.log_error(
                    f"Failed to contact {agent_name}: {str(e)}",
                    error_type="communication",
                    correlation_id=correlation_id
                )
                
                return {
                    "error": f"Failed to contact {agent_name}",
                    "details": str(e)
                }
        
        @self.server.tool
        async def get_connections(ctx: Context) -> Dict[str, Any]:
            """Get list of available agent connections."""
            return {
                "agent": self.agent_id,
                "connections": self.available_connections,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
        
        @self.server.tool
        async def communicate_with_agent(
            ctx: Context,
            from_agent: str,
            message: str,
            conversation_id: Optional[str] = None
        ) -> Dict[str, Any]:
            """Handle incoming communication from another agent."""
            correlation_id = str(uuid.uuid4())
            conv_id = conversation_id or str(uuid.uuid4())
            
            # Log incoming message
            self.logger.log_tool_call_received(
                tool_name="communicate_with_agent",
                from_agent=from_agent,
                payload={"message": message, "conversation_id": conv_id},
                correlation_id=correlation_id
            )
            
            try:
                # Build system prompt
                system_prompt = self._build_agent_system_prompt()
                
                # Build specific prompt for agent-to-agent communication
                agent_system_prompt = f"""You are Agent {self.agent_id}. {self.agent_role}

You are responding to a message from {from_agent}, another agent in the system.

IMPORTANT: Provide a direct, helpful answer to their message.
- DO NOT use tool code or markdown formatting
- DO NOT try to call tools (you have none available in this context)
- Simply answer their question or respond to their request directly

Be concise and helpful."""
                
                # Simple conversation
                messages = [
                    {"role": "system", "content": agent_system_prompt},
                    {"role": "user", "content": f"Message from {from_agent}: {message}"}
                ]
                
                # For agent-to-agent communication, we don't provide tools
                # to avoid infinite loops where agents keep calling each other
                response = await self.llm.complete(
                    messages=messages,
                    tools=[],  # No tools for agent-to-agent communication
                    temperature=0.7
                )
                
                return {
                    "response": response.content,
                    "conversation_id": conv_id,
                    "agent": self.agent_id
                }
                
            except Exception as e:
                self.logger.log_error(
                    str(e),
                    error_type="agent_communication",
                    correlation_id=correlation_id
                )
                
                return {
                    "error": f"Failed to process message: {str(e)}",
                    "conversation_id": conv_id,
                    "agent": self.agent_id
                }
        
        @self.server.tool
        async def chat_with_user(
            ctx: Context,
            message: str,
            conversation_id: Optional[str] = None
        ) -> Dict[str, Any]:
            """Handle direct user interaction."""
            correlation_id = str(uuid.uuid4())
            conv_id = conversation_id or str(uuid.uuid4())
            
            self.logger.log_tool_call_received(
                tool_name="chat_with_user",
                from_agent="user",
                payload={"message": message, "conversation_id": conv_id},
                correlation_id=correlation_id
            )
            
            try:
                # Build user-specific system prompt
                user_prompt = f"""You are Agent {self.agent_id}, directly chatting with a human user.

Your specialized role: {self.agent_role}

You have access to these tools:
- contact_agent(agent_name, message): Send a message to another agent
- get_connections(): List available agents

Current connections: {', '.join(self.available_connections) if self.available_connections else 'None'}

IMPORTANT RULES:
1. Use contact_agent (NOT communicate_with_agent) to send messages
2. After receiving a response from another agent, provide a final answer to the user
3. Do NOT keep using tools repeatedly - once you get a response, summarize and respond
4. Be helpful but concise"""
                
                messages = [
                    {"role": "system", "content": user_prompt},
                    {"role": "user", "content": message}
                ]
                
                # Get response with tools
                response = await self.llm.complete(
                    messages=messages,
                    tools=self._get_agent_tools(),
                    temperature=0.7
                )
                
                # Handle tool calls similar to communicate_with_agent
                max_iterations = 5  # Prevent infinite loops
                iteration = 0
                
                while response.tool_calls is not None and len(response.tool_calls) > 0 and iteration < max_iterations:
                    iteration += 1
                    self.logger.info(f"Tool call iteration {iteration}, processing {len(response.tool_calls)} calls")
                    tool_results = []
                    
                    for tool_call in response.tool_calls:
                        self.logger.info(f"Processing tool call: {tool_call.tool} with params: {tool_call.parameters}")
                        
                        if tool_call.tool == "contact_agent":
                            # Execute via MCP client
                            target_agent = tool_call.parameters.get("agent_name")
                            message = tool_call.parameters.get("message", "")
                            
                            if self.mcp_client and target_agent in self.available_connections:
                                try:
                                    result = await self.mcp_client.communicate_with_agent(
                                        target_agent=target_agent,
                                        message=message,
                                        conversation_id=tool_call.parameters.get("conversation_id")
                                    )
                                    tool_results.append(result.data if hasattr(result, 'data') else result)
                                except Exception as e:
                                    self.logger.error(f"Failed to contact {target_agent}: {e}")
                                    tool_results.append({"error": f"Failed to contact {target_agent}: {str(e)}"})
                            else:
                                self.logger.error(f"Agent {target_agent} not in available connections: {self.available_connections}")
                                tool_results.append({"error": f"Agent {target_agent} not available"})
                        elif tool_call.tool == "get_connections":
                            tool_results.append({"connections": self.available_connections})
                        else:
                            self.logger.warning(f"Unknown tool call: {tool_call.tool}")
                            tool_results.append({"error": f"Unknown tool: {tool_call.tool}"})
                    
                    # Add tool call to conversation
                    # Keep it simple to avoid pattern matching issues
                    messages.append({
                        "role": "assistant",
                        "content": "Let me check with the other agent for you."
                    })
                    
                    # Add tool results in a clearer format with guidance
                    if tool_results and isinstance(tool_results[0], dict) and 'response' in tool_results[0]:
                        agent_name = tool_results[0].get('agent', 'agent')
                        agent_response = tool_results[0]['response'].strip()
                        result_text = f"Response from {agent_name}: {agent_response}\n\nIMPORTANT: You have received the answer. Now provide a natural, conversational response to the user. Do NOT output any tool code or markdown. Just answer naturally based on what {agent_name} told you."
                    else:
                        result_text = str(tool_results)
                    
                    messages.append({
                        "role": "tool",
                        "content": result_text
                    })
                    
                    # Check if we got a successful response from another agent
                    got_agent_response = (tool_results and 
                                        isinstance(tool_results[0], dict) and 
                                        'response' in tool_results[0] and 
                                        'error' not in tool_results[0])
                    
                    # If we got a response, modify the last message to include instruction
                    if got_agent_response:
                        # Add a user message to prompt for final response
                        agent_name = tool_results[0].get('agent', 'agent') 
                        agent_answer = tool_results[0]['response'].strip()
                        messages.append({
                            "role": "user",
                            "content": f"Great! {agent_name} told you that the answer is: {agent_answer}. Now please tell me the answer in your own words as a complete sentence."
                        })
                    
                    # Get next response
                    # If we got a good response from another agent, don't provide tools
                    # This forces the LLM to provide a final answer
                    response = await self.llm.complete(
                        messages=messages,
                        tools=[] if got_agent_response else self._get_agent_tools(),
                        temperature=0.7
                    )
                
                if iteration >= max_iterations:
                    self.logger.warning("Reached max tool call iterations")
                
                return {
                    "response": response.content,
                    "conversation_id": conv_id,
                    "agent": self.agent_id
                }
                
            except Exception as e:
                self.logger.log_error(
                    str(e),
                    error_type="user_chat",
                    correlation_id=correlation_id
                )
                
                return {
                    "error": f"Failed to process message: {str(e)}",
                    "conversation_id": conv_id,
                    "agent": self.agent_id
                }
    
    def _get_agent_tools(self) -> List[ToolDefinition]:
        """Get list of tools the agent's LLM can use.
        
        With universal approach, we only need one tool for all agents.
        """
        tools = []
        
        # Single universal tool for agent communication
        tools.append(ToolDefinition(
            name="contact_agent",
            description="Send a message to any connected agent",
            parameters={
                "type": "object",
                "properties": {
                    "agent_name": {
                        "type": "string",
                        "description": "Name of the agent to contact"
                    },
                    "message": {
                        "type": "string",
                        "description": "The message to send"
                    },
                    "conversation_id": {
                        "type": "string",
                        "description": "Optional conversation ID"
                    }
                },
                "required": ["agent_name", "message"]
            }
        ))
        
        # Tool to check available connections
        tools.append(ToolDefinition(
            name="get_connections",
            description="Get list of agents you can contact",
            parameters={
                "type": "object",
                "properties": {},
                "required": []
            }
        ))
        
        return tools
    
    async def run(self, port: int):
        """Run the MCP server."""
        self.logger.info(f"Starting Universal MCP Server on port {port}")
        await self.server.run_async(transport="http", port=port)
