"""Simple control socket for agent commands."""

import asyncio
import json
import os
from ..core.logging import AgentLogger


class AgentControlSocket:
    """Handles control commands via Unix socket."""
    
    def __init__(self, agent, socket_path: str, shutdown_event=None):
        self.agent = agent
        self.socket_path = socket_path
        self.shutdown_event = shutdown_event
        self._event_subscription = None
        # Use the agent's logger if available, otherwise create a basic one
        self.logger = agent.logger if hasattr(agent, 'logger') else AgentLogger(
            agent_id=agent.agent_id if hasattr(agent, 'agent_id') else 'control_socket',
            log_level='INFO'
        )
    
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
            
            elif cmd['cmd'] == 'subscribe_events':
                # Subscribe to agent events and stream them
                response = {'status': 'subscribed'}
                
                # Send initial response
                writer.write(json.dumps(response).encode() + b'\n')
                await writer.drain()
                
                # Set up event forwarding
                if hasattr(self.agent, 'event_stream'):
                    async def forward_event(event):
                        # Forward event to client
                        try:
                            event_data = {
                                'event': {
                                    'type': event.event_type,
                                    'agent_id': event.agent_id,
                                    'data': event.data,
                                    'timestamp': event.timestamp.isoformat()
                                }
                            }
                            writer.write(json.dumps(event_data).encode() + b'\n')
                            await writer.drain()
                        except Exception as e:
                            # Connection closed, unsubscribe
                            self.logger.debug(f"Event forwarding error: {e}")
                            if hasattr(self.agent, 'event_stream'):
                                self.agent.event_stream.unsubscribe(forward_event)
                    
                    # Subscribe to agent's event stream
                    unsubscribe_func = self.agent.event_stream.subscribe(forward_event)
                    self._event_subscription = unsubscribe_func
                    self.logger.info(f"Subscribed to event stream for {self.agent.agent_id}, subscribers: {len(self.agent.event_stream.subscribers)}")
                    
                    # Keep connection open for streaming events
                    try:
                        # Wait indefinitely while connection is open
                        while True:
                            # Check if connection is still alive
                            await asyncio.sleep(1)
                            # The events are sent via forward_event callback
                    except (ConnectionResetError, BrokenPipeError):
                        # Client disconnected
                        pass
                    finally:
                        # Unsubscribe when connection closes
                        if hasattr(self.agent, 'event_stream'):
                            self.agent.event_stream.unsubscribe(forward_event)
                    
                    return  # Skip normal response/cleanup
                else:
                    response = {'error': 'Event stream not available'}
            
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
            # Unsubscribe from events if subscribed
            if hasattr(self, '_event_subscription') and self._event_subscription and hasattr(self.agent, 'event_stream'):
                try:
                    self.agent.event_stream.unsubscribe(self._event_subscription)
                except:
                    pass
                self._event_subscription = None
                
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
