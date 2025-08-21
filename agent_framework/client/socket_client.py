"""Unified socket client for agent communication."""

import asyncio
import json
import os
from typing import Dict, Any, Optional


class AgentSocketClient:
    """Unified client for agent socket communication.
    
    This eliminates all duplicated socket communication code across the codebase.
    """
    
    @staticmethod
    async def send_command(
        agent_name: str, 
        command: Dict[str, Any], 
        timeout: float = 5.0
    ) -> Dict[str, Any]:
        """Send any command to an agent via socket.
        
        This is the single source of truth for socket communication.
        """
        socket_path = f"/tmp/chaotic-af/agent-{agent_name}.sock"
        
        if not os.path.exists(socket_path):
            return {"error": f"Socket not found for agent {agent_name}"}
        
        try:
            reader, writer = await asyncio.wait_for(
                asyncio.open_unix_connection(socket_path),
                timeout=timeout
            )
            
            # Send command
            writer.write(json.dumps(command).encode() + b'\n')
            await writer.drain()
            
            # Read response
            response = await asyncio.wait_for(
                reader.readline(),
                timeout=timeout
            )
            
            # Close connection
            writer.close()
            await writer.wait_closed()
            
            return json.loads(response.decode())
            
        except asyncio.TimeoutError:
            return {"error": f"Timeout connecting to {agent_name}"}
        except Exception as e:
            return {"error": f"Failed to communicate with {agent_name}: {str(e)}"}
    
    @classmethod
    async def health_check(cls, agent_name: str, timeout: float = 5.0) -> Dict[str, Any]:
        """Check agent health."""
        return await cls.send_command(agent_name, {"cmd": "health"}, timeout)
    
    @classmethod
    async def connect_agents(
        cls, 
        from_agent: str, 
        to_agent: str, 
        to_endpoint: str,
        timeout: float = 5.0
    ) -> Dict[str, Any]:
        """Connect one agent to another."""
        return await cls.send_command(from_agent, {
            "cmd": "connect",
            "target": to_agent,
            "endpoint": to_endpoint
        }, timeout)
    
    @classmethod
    async def shutdown_agent(cls, agent_name: str, timeout: float = 5.0) -> Dict[str, Any]:
        """Shutdown an agent gracefully."""
        return await cls.send_command(agent_name, {"cmd": "shutdown"}, timeout)
    
    @classmethod
    async def get_metrics(
        cls, 
        agent_name: str, 
        format: str = "json",
        timeout: float = 5.0
    ) -> Dict[str, Any]:
        """Get agent metrics."""
        return await cls.send_command(agent_name, {
            "cmd": "metrics",
            "format": format
        }, timeout)
    
    @staticmethod
    async def subscribe_events(agent_name: str, event_handler: callable) -> asyncio.Task:
        """Subscribe to agent events. Returns a task that streams events."""
        socket_path = f"/tmp/chaotic-af/agent-{agent_name}.sock"
        
        if not os.path.exists(socket_path):
            raise FileNotFoundError(f"Socket not found for agent {agent_name}")
        
        async def event_stream():
            reader, writer = await asyncio.open_unix_connection(socket_path)
            
            try:
                # Send subscribe command
                cmd = {"cmd": "subscribe_events"}
                writer.write(json.dumps(cmd).encode() + b'\n')
                await writer.drain()
                
                # Read initial response
                response = await reader.readline()
                result = json.loads(response.decode())
                
                if result.get('status') != 'subscribed':
                    raise Exception(f"Failed to subscribe: {result}")
                
                # Stream events
                while True:
                    line = await reader.readline()
                    if not line:
                        break
                    
                    data = json.loads(line.decode())
                    if 'event' in data:
                        await event_handler(data['event'])
                        
            finally:
                writer.close()
                await writer.wait_closed()
        
        # Return the task so caller can manage it
        return asyncio.create_task(event_stream())
