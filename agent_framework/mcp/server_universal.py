"""Universal Agent MCP Server with dynamic tool discovery.

Agents discover and use tools from other connected agents' MCP servers directly,
following proper MCP architecture principles.
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
    """MCP Server that exposes agent functionality to other agents and users."""
    
    def __init__(
        self,
        agent_id: str,
        agent_role: str,
        llm_provider: LLMProvider,
        event_stream: EventStream,
        logger: AgentLogger,
        mcp_client: Optional['AgentMCPClient'] = None,
        chaos_mode: bool = False
    ):
        self.agent_id = agent_id
        self.agent_role = agent_role
        self.llm = llm_provider
        self.event_stream = event_stream
        self.logger = logger
        self.mcp_client = mcp_client
        self.chaos_mode = chaos_mode
        
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

To communicate with other agents, use the communicate_with_<agent_name> tools that are available to you.
For example: communicate_with_alice(message="Hello Alice!")

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
        
        # NOTE: contact_agent tool has been removed
        # Agents now use communicate_with_<agent_name> tools discovered from other agents' MCP servers
        # This follows proper MCP architecture where agents call each other's exposed tools directly
        
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
                if self.chaos_mode:
                    agent_system_prompt = f"""You are Agent {self.agent_id} with expertise in: {self.agent_role}

Colleague {from_agent} is asking you something. Available team members: {', '.join(self.available_connections) if self.available_connections else 'None'}

NATURAL TEAM MEMBER BEHAVIOR:

EVALUATE THE REQUEST:
"Can I answer this completely with just my expertise, or do I need input from others?"

IF YOU'RE THE RIGHT EXPERT:
- Provide your expert perspective directly
- If you think another colleague should also weigh in, suggest it: "You should also check with [colleague] about [specific aspect]"

IF YOU NEED MORE CONTEXT:
- Think: "Who else would have the missing piece of this puzzle?"
- Consult that person FIRST using communicate_with_<agent> tools
- Give {from_agent} a complete answer based on combined input

IF SOMEONE ELSE IS MORE QUALIFIED:
- Think: "This is really more [other_agent]'s area of expertise"
- Consult with that expert first
- Either coordinate the response or suggest {from_agent} talk to them directly

BE NATURAL:
- Don't consult everyone for simple questions (that's not human)
- DO consult others when you genuinely need their expertise
- Think like a real team member: "What would I actually do in this situation?"
- Help create organic discussion flow, not artificial coordination

PEER DISCUSSION RULE:
If {from_agent} asks you something that would benefit from another colleague's input, 
don't just suggest they talk to that person - actually facilitate the discussion by 
consulting that colleague yourself and providing a more complete response.

EXAMPLE: If backend asks about API design and it affects frontend, don't just say 
"talk to frontend" - actually consult frontend_dev and give backend a complete answer."""
                else:
                    agent_system_prompt = f"""You are Agent {self.agent_id}. {self.agent_role}

You are responding to a message from {from_agent}, another agent in the system.

GUARDRAIL MODE: You should provide direct answers to avoid infinite loops.
- Provide a helpful, direct response to their message
- Do not try to call other agents (tools are disabled for safety)
- Be concise and helpful in your response"""
                
                # Simple conversation
                messages = [
                    {"role": "system", "content": agent_system_prompt},
                    {"role": "user", "content": f"Message from {from_agent}: {message}"}
                ]
                
                # Chaos mode: Give agents tool access for chain reactions if enabled
                available_tools = []
                if self.chaos_mode and self.mcp_client:
                    available_tools = await self.mcp_client.get_available_agent_tools()
                    self.logger.info(f"CHAOS MODE ENABLED: Agent has access to {len(available_tools)} agent tools")
                else:
                    self.logger.info("GUARDRAIL MODE: Agent has no tool access (prevents infinite loops)")
                
                response = await self.llm.complete(
                    messages=messages,
                    tools=available_tools,  # Tools available only in chaos mode
                    temperature=0.7
                )
                
                # Handle tool calls only if chaos mode is enabled
                if self.chaos_mode and response.tool_calls is not None:
                    max_iterations = 5  # Prevent infinite loops
                    iteration = 0
                    
                while self.chaos_mode and response.tool_calls is not None and iteration < max_iterations:
                    iteration += 1
                    self.logger.info(f"Agent communication iteration {iteration}, processing {len(response.tool_calls)} calls")
                    
                    # Process each tool call
                    for tool_call in response.tool_calls:
                        self.logger.info(f"Processing tool call: {tool_call.tool} with params: {tool_call.parameters}")
                        
                        # Handle agent communication tools
                        if tool_call.tool.startswith("communicate_with_"):
                            target_agent = tool_call.tool.replace("communicate_with_", "")
                            message = tool_call.parameters.get("message", "")
                            
                            # Call the other agent - POTENTIAL FOR CHAOS!
                            result = await self.mcp_client.communicate_with_agent(
                                target_agent=target_agent,
                                message=message,
                                conversation_id=conv_id
                            )
                            
                            # Feed result back to LLM for next iteration
                            messages.append({
                                "role": "assistant", 
                                "content": response.content,
                                "tool_calls": [{"id": tool_call.id, "type": "function", "function": {"name": tool_call.tool, "arguments": tool_call.parameters}}]
                            })
                            messages.append({
                                "role": "tool",
                                "content": str(result.get('response', '')),
                                "tool_call_id": tool_call.id
                            })
                    
                    # Get next response with tool results
                    response = await self.llm.complete(
                        messages=messages,
                        tools=available_tools,  # Keep tools available for MORE CHAOS!
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
                # Get available tools from connected agents
                available_tools = []
                if self.mcp_client:
                    available_tools = await self.mcp_client.get_available_agent_tools()
                
                # Build user-specific system prompt
                connected_agents = ', '.join(self.available_connections) if self.available_connections else 'None'
                tool_descriptions = []
                for tool in available_tools:
                    agent_name = tool.name.replace("communicate_with_", "")
                    tool_descriptions.append(f"- communicate_with_{agent_name}: Send a message to {agent_name}")
                
                user_prompt = f"""You are Agent {self.agent_id} with expertise in: {self.agent_role}

Connected team members: {connected_agents}
Available communication tools: {chr(10).join(tool_descriptions) if tool_descriptions else '- No team members connected'}

HUMAN-LIKE TEAM BEHAVIOR:

FIRST ASK YOURSELF: "Am I the BEST person to handle this request alone?"

IF YES (request matches your core expertise):
- Handle it directly with confidence
- Optionally consult 1-2 relevant colleagues if you need their input

IF NO (request spans multiple areas or you're not the expert):
- Think: "Who would be better positioned to handle this?"
- Think: "What aspects need input from other specialists?"
- Consult with relevant team members BEFORE responding
- Don't be the bottleneck - let the right experts lead

NATURAL CONSULTATION FLOW:
1. Identify the PRIMARY expert for this request
2. If that's you: handle directly (maybe consult 1-2 others)
3. If that's someone else: consult them, then assess if MORE input needed
4. Continue until you have sufficient expert input
5. Provide user with well-informed response

BE HUMAN-LIKE:
- Don't immediately broadcast to everyone (that's not natural)
- Start with most relevant person, see what they say
- Let their response guide who ELSE to talk to
- Think: "Would a human team member consult more people for this?"

CRITICAL RULE: 
If you tell the user "I'll consult with X, Y, Z" then you MUST actually do those consultations using communicate_with_<agent> tools BEFORE responding. 
NEVER promise to consult and then respond immediately - that's artificial behavior.

Eventually give user comprehensive answer from team perspective after ACTUAL consultations."""
                
                messages = [
                    {"role": "system", "content": user_prompt},
                    {"role": "user", "content": message}
                ]
                
                # Get response with tools
                response = await self.llm.complete(
                    messages=messages,
                    tools=available_tools,
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
                        
                        if tool_call.tool.startswith("communicate_with_"):
                            # Extract target agent from tool name
                            target_agent = tool_call.tool.replace("communicate_with_", "")
                            message = tool_call.parameters.get("message", "")
                            
                            # Note: Event emission is handled by mcp_client.communicate_with_agent
                            
                            if self.mcp_client and target_agent in self.available_connections:
                                try:
                                    result = await self.mcp_client.communicate_with_agent(
                                        target_agent=target_agent,
                                        message=message,
                                        conversation_id=conv_id
                                    )
                                    tool_results.append(result.data if hasattr(result, 'data') else result)
                                    # Note: Response event emission is handled by mcp_client.communicate_with_agent
                                except Exception as e:
                                    self.logger.error(f"Failed to communicate with {target_agent}: {e}")
                                    tool_results.append({"error": f"Failed to communicate with {target_agent}: {str(e)}"})
                            else:
                                self.logger.error(f"Agent {target_agent} not in available connections: {self.available_connections}")
                                tool_results.append({"error": f"Agent {target_agent} not available"})
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
        """DEPRECATED: This method is no longer used.
        
        Agents now discover tools from other agents' MCP servers dynamically.
        Tools are fetched via mcp_client.get_available_agent_tools().
        """
        # This method is kept for backward compatibility but should not be used
        return []
    
    async def run(self, port: int):
        """Run the MCP server."""
        self.logger.info(f"Starting Universal MCP Server on port {port}")
        await self.server.run_async(transport="http", port=port)
