"""Simple control socket for agent commands."""

import asyncio
import json
import os


class AgentControlSocket:
    """Handles control commands via Unix socket."""
    
    def __init__(self, agent, socket_path: str, shutdown_event=None):
        self.agent = agent
        self.socket_path = socket_path
        self.shutdown_event = shutdown_event
    
    async def start(self):
        """Start the control socket server."""
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.socket_path), exist_ok=True)
        
        # Remove old socket if exists
        if os.path.exists(self.socket_path):
            os.unlink(self.socket_path)
        
        # Create server
        server = await asyncio.start_unix_server(
            self._handle_connection,
            self.socket_path
        )
        
        return server
    
    async def _handle_connection(self, reader, writer):
        """Handle a single control connection."""
        try:
            # Read command
            data = await reader.readline()
            if not data:
                return
                
            cmd = json.loads(data.decode())
            
            # Process command
            if cmd['cmd'] == 'health':
                response = {'status': 'ready'}
            
            elif cmd['cmd'] == 'connect':
                # Add connection to agent
                success = await self.agent.mcp_client.add_connection(
                    cmd['target'],
                    cmd['endpoint']
                )
                
                # Update server if needed
                if hasattr(self.agent.mcp_server, 'update_connections'):
                    connections = list(self.agent.mcp_client.connections.keys())
                    self.agent.mcp_server.update_connections(connections)
                
                response = {'status': 'connected' if success else 'failed'}
            
            elif cmd['cmd'] == 'shutdown':
                # Trigger shutdown
                if hasattr(self.agent, '_shutdown_event'):
                    self.agent._shutdown_event.set()
                if self.shutdown_event:
                    self.shutdown_event.set()
                response = {'status': 'shutting_down'}
                
                # Schedule socket cleanup after response
                asyncio.create_task(self._cleanup_socket())
            
            elif cmd['cmd'] == 'metrics':
                # Return metrics in requested format
                format_type = cmd.get('format', 'json')
                
                if hasattr(self.agent, 'metrics_collector'):
                    if format_type == 'prometheus':
                        metrics_text = self.agent.metrics_collector.get_metrics_prometheus()
                        response = {'metrics': metrics_text}
                    else:
                        metrics_json = self.agent.metrics_collector.get_metrics_json()
                        response = {'metrics': metrics_json}
                else:
                    response = {'error': 'Metrics not available'}
            
            else:
                response = {'error': f"Unknown command: {cmd['cmd']}"}
            
            # Send response
            writer.write(json.dumps(response).encode() + b'\n')
            await writer.drain()
            
        except Exception as e:
            # Send error
            error_response = {'error': str(e)}
            writer.write(json.dumps(error_response).encode() + b'\n')
            await writer.drain()
        
        finally:
            writer.close()
            await writer.wait_closed()
    
    async def _cleanup_socket(self):
        """Clean up socket file after shutdown."""
        await asyncio.sleep(0.5)  # Brief delay to ensure response is sent
        if os.path.exists(self.socket_path):
            try:
                os.unlink(self.socket_path)
            except:
                pass
