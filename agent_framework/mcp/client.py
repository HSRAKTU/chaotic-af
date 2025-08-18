"""Master MCP Client implementation for agent connections.

Requirements:
- Connect to other agent MCP servers
- Connect to external MCP servers (tools)
- Handle connection failures gracefully
- Maintain connection pool
- Full logging of all client operations
"""

import asyncio
from typing import Dict, Any, Optional, List
import uuid

from fastmcp import Client
from ..core.events import EventStream, EventType
from ..core.logging import AgentLogger


class MCPConnection:
    """Represents a connection to an MCP server."""
    
    def __init__(self, name: str, url: str, client: Optional[Client] = None):
        self.name = name
        self.url = url
        self.client = client
        self.connected = False
        self.is_agent = url.startswith("http://")  # Agent servers use HTTP
        self.last_error: Optional[str] = None


class AgentMCPClient:
    """Master MCP Client that manages connections to other agents and tools."""
    
    def __init__(
        self,
        agent_id: str,
        event_stream: EventStream,
        logger: AgentLogger
    ):
        self.agent_id = agent_id
        self.event_stream = event_stream
        self.logger = logger
        self.connections: Dict[str, MCPConnection] = {}
        self._connection_lock = asyncio.Lock()
    
    async def add_connection(self, name: str, url: str) -> bool:
        """Add a new MCP server connection.
        
        Args:
            name: Friendly name for the connection (agent name or tool name)
            url: MCP server URL (http://... for agents, stdio://... for tools)
        
        Returns:
            True if connection was established successfully
        """
        async with self._connection_lock:
            if name in self.connections:
                self.logger.warning(f"Connection {name} already exists")
                return False
            
            # Create connection object
            conn = MCPConnection(name, url)
            self.connections[name] = conn
            
            # Try to establish connection
            return await self._connect(conn)
    
    async def _connect(self, conn: MCPConnection) -> bool:
        """Establish connection to an MCP server."""
        try:
            self.logger.info(f"Connecting to MCP server: {conn.name} at {conn.url}")
            
            # Create client
            conn.client = Client(conn.url)
            
            # Connect
            await conn.client.__aenter__()
            conn.connected = True
            
            # Log available tools
            if conn.is_agent:
                # For agent connections, we expect specific tools
                tools = await conn.client.list_tools()
                self.logger.debug(
                    f"Connected to agent {conn.name}. Available tools: "
                    f"{[t.name for t in tools]}"
                )
            else:
                # For external tools, log what's available
                tools = await conn.client.list_tools()
                self.logger.info(
                    f"Connected to tool server {conn.name}. "
                    f"Available tools: {[t.name for t in tools]}"
                )
            
            await self.event_stream.emit(
                EventType.TOOL_CALL_RESPONSE,
                {
                    "action": "connection_established",
                    "target": conn.name,
                    "url": conn.url,
                    "tools": [t.name for t in tools]
                }
            )
            
            return True
            
        except Exception as e:
            conn.last_error = str(e)
            conn.connected = False
            
            self.logger.log_error(
                f"Failed to connect to {conn.name}: {str(e)}",
                error_type="connection"
            )
            
            await self.event_stream.emit(
                EventType.ERROR,
                {
                    "error": str(e),
                    "context": f"connecting_to_{conn.name}",
                    "url": conn.url
                }
            )
            
            return False
    
    async def communicate_with_agent(
        self, 
        target_agent: str, 
        message: str,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Send a message to another agent.
        
        This is called when the LLM wants to contact another agent.
        """
        correlation_id = str(uuid.uuid4())
        
        # Check if we have a connection to this agent
        if target_agent not in self.connections:
            error_msg = f"No connection to agent {target_agent}"
            self.logger.log_error(error_msg, error_type="agent_communication")
            return {"error": error_msg}
        
        conn = self.connections[target_agent]
        
        # Check if connected
        if not conn.connected:
            # Try to reconnect
            if not await self._connect(conn):
                return {
                    "error": f"Cannot connect to agent {target_agent}: {conn.last_error}"
                }
        
        # Log outgoing call
        self.logger.log_tool_call_making(
            tool_name="communicate_with_agent",
            to_target=target_agent,
            payload={
                "from_agent": self.agent_id,
                "message": message,
                "conversation_id": conversation_id
            },
            correlation_id=correlation_id
        )
        
        # Emit event
        await self.event_stream.emit(
            EventType.TOOL_CALL_MAKING,
            {
                "tool": "communicate_with_agent",
                "target": target_agent,
                "payload": {
                    "from_agent": self.agent_id,
                    "message": message
                }
            },
            correlation_id
        )
        
        try:
            # Call the communicate_with_agent tool on the target agent
            result = await conn.client.call_tool(
                "communicate_with_agent",
                {
                    "from_agent": self.agent_id,
                    "message": message,
                    "conversation_id": conversation_id
                }
            )
            
            # Log response
            self.logger.log_tool_response(
                tool_name="communicate_with_agent",
                response=result,
                success=True,
                correlation_id=correlation_id
            )
            
            # Emit response event
            await self.event_stream.emit(
                EventType.TOOL_CALL_RESPONSE,
                {
                    "tool": "communicate_with_agent",
                    "target": target_agent,
                    "response": result
                },
                correlation_id
            )
            
            return result
            
        except Exception as e:
            error_msg = f"Failed to communicate with agent {target_agent}: {str(e)}"
            
            self.logger.log_tool_response(
                tool_name="communicate_with_agent",
                response={"error": error_msg},
                success=False,
                correlation_id=correlation_id
            )
            
            # Mark connection as failed
            conn.connected = False
            conn.last_error = str(e)
            
            return {"error": error_msg}
    
    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        arguments: Dict[str, Any]
    ) -> Any:
        """Call a tool on an external MCP server.
        
        This is for non-agent MCP servers (like web search, database, etc).
        """
        correlation_id = str(uuid.uuid4())
        
        # Check connection
        if server_name not in self.connections:
            error_msg = f"No connection to server {server_name}"
            self.logger.log_error(error_msg, error_type="tool_call")
            return {"error": error_msg}
        
        conn = self.connections[server_name]
        
        # Ensure connected
        if not conn.connected:
            if not await self._connect(conn):
                return {
                    "error": f"Cannot connect to server {server_name}: {conn.last_error}"
                }
        
        # Log tool call
        self.logger.log_tool_call_making(
            tool_name=f"{server_name}.{tool_name}",
            to_target=server_name,
            payload=arguments,
            correlation_id=correlation_id
        )
        
        try:
            # Call the tool
            result = await conn.client.call_tool(tool_name, arguments)
            
            self.logger.log_tool_response(
                tool_name=f"{server_name}.{tool_name}",
                response=result,
                success=True,
                correlation_id=correlation_id
            )
            
            return result
            
        except Exception as e:
            error_msg = f"Tool call failed: {str(e)}"
            
            self.logger.log_tool_response(
                tool_name=f"{server_name}.{tool_name}",
                response={"error": error_msg},
                success=False,
                correlation_id=correlation_id
            )
            
            return {"error": error_msg}
    
    async def get_agent_status(self, agent_name: str) -> Dict[str, Any]:
        """Get status of another agent."""
        if agent_name not in self.connections:
            return {"error": f"No connection to agent {agent_name}"}
        
        conn = self.connections[agent_name]
        if not conn.connected:
            return {
                "agent": agent_name,
                "status": "disconnected",
                "last_error": conn.last_error
            }
        
        try:
            # Call get_agent_status tool
            return await conn.client.call_tool("get_agent_status", {})
        except Exception as e:
            return {
                "agent": agent_name,
                "status": "error",
                "error": str(e)
            }
    
    async def close_all(self):
        """Close all connections gracefully."""
        self.logger.info("Closing all MCP client connections")
        
        async with self._connection_lock:
            for name, conn in self.connections.items():
                if conn.connected and conn.client:
                    try:
                        await conn.client.__aexit__(None, None, None)
                        self.logger.debug(f"Closed connection to {name}")
                    except Exception as e:
                        self.logger.warning(f"Error closing connection to {name}: {e}")
                
                conn.connected = False
            
            self.connections.clear()
    
    def get_connection_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all connections."""
        return {
            name: {
                "url": conn.url,
                "connected": conn.connected,
                "is_agent": conn.is_agent,
                "last_error": conn.last_error
            }
            for name, conn in self.connections.items()
        }
