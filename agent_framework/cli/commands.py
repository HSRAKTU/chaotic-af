"""CLI commands for managing agents.

Requirements:
- Start/stop individual agents or all agents
- Show agent status
- Follow logs
- Connect agents
- Simple, intuitive interface
"""

import click
import asyncio
import json
import yaml
from pathlib import Path
from typing import List, Optional
import sys
import os
import signal
import atexit
import psutil

from ..core.config import load_config, AgentConfig
from ..network.supervisor import AgentSupervisor
from ..network.registry import AgentRegistry


# Global state file to track running agents
STATE_FILE = Path.home() / ".chaotic-af" / "agents.json"


def load_state():
    """Load agent state from file."""
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r') as f:
            return json.load(f)
    return {"agents": {}}


def save_state(state):
    """Save agent state to file."""
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        json.dump(state, f, indent=2)


def cleanup_agents_on_exit():
    """Clean up any running agent processes on exit."""
    try:
        # Kill any agent_framework.network.agent_runner processes
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if cmdline and 'agent_framework.network.agent_runner' in ' '.join(cmdline):
                    proc.terminate()
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except Exception:
        pass


@click.group()
@click.pass_context
def cli(ctx):
    """Chaotic AF - Manage multi-agent systems with ease."""
    ctx.ensure_object(dict)
    ctx.obj['state'] = load_state()


@cli.command()
@click.argument('config_files', nargs=-1, required=True, type=click.Path(exists=True))
@click.option('--connect-all', '-c', is_flag=True, help='Connect all agents bidirectionally')
@click.pass_context
def start(ctx, config_files: tuple, connect_all: bool):
    """Start agent(s) from configuration file(s).
    
    Examples:
        agentctl start agent1.yaml
        agentctl start agent1.yaml agent2.yaml agent3.yaml --connect-all
    """
    state = ctx.obj['state']
    
    # Register cleanup on exit
    atexit.register(cleanup_agents_on_exit)
    
    # Create new supervisor for this batch
    supervisor = AgentSupervisor()
    
    # Load configurations
    configs = []
    for config_file in config_files:
        try:
            config = load_config(config_file)
            configs.append(config)
            supervisor.add_agent(config)
            click.echo(f"✓ Loaded configuration for agent '{config.name}'")
        except Exception as e:
            click.echo(f"✗ Failed to load {config_file}: {str(e)}", err=True)
            sys.exit(1)
    
    # Start agents
    async def start_agents():
        # Start all agents without background monitoring
        await supervisor.start_all(monitor=False)
        
        # Save agent info to state
        for config in configs:
            agent_proc = supervisor.agents.get(config.name)
            if agent_proc and agent_proc.status == "running":
                state['agents'][config.name] = {
                    'pid': agent_proc.pid,
                    'port': config.port,
                    'config_file': str(Path(config_file).absolute()),
                    'status': 'running'
                }
        
        save_state(state)
        
        click.echo("\n✓ All agents started successfully!")
        
        # Show status
        click.echo("\nAgent Status:")
        for config in configs:
            agent_proc = supervisor.agents.get(config.name)
            if agent_proc:
                click.echo(f"  {config.name}: running (PID: {agent_proc.pid}, port {config.port})")
        
        if connect_all and len(configs) > 1:
            click.echo("\nConnecting agents...")
            # Connect all agents bidirectionally
            for i, config1 in enumerate(configs):
                for config2 in configs[i+1:]:
                    await supervisor.connect(config1.name, config2.name)
                    await supervisor.connect(config2.name, config1.name)
            click.echo("✓ All agents connected bidirectionally")
    
    # Run async function and then exit
    try:
        # Use asyncio.run for cleaner lifecycle management
        asyncio.run(start_agents())
    except KeyboardInterrupt:
        click.echo("\nInterrupted")
        sys.exit(1)
    
    click.echo("\nAgents are running in the background.")
    click.echo("Use 'agentctl status' to check their status.")
    click.echo("Use 'agentctl logs <agent>' to see agent logs.")
    click.echo("Use 'agentctl stop' to stop all agents.")


@cli.command()
@click.argument('agent_names', nargs=-1)
@click.pass_context
def stop(ctx, agent_names: tuple):
    """Stop agent(s).
    
    Examples:
        agentctl stop              # Stop all agents
        agentctl stop agent1       # Stop specific agent
        agentctl stop agent1 agent2
    """
    state = ctx.obj['state']
    
    agents_to_stop = agent_names if agent_names else list(state['agents'].keys())
    
    for name in agents_to_stop:
        if name in state['agents']:
            agent_info = state['agents'][name]
            pid = agent_info['pid']
            
            try:
                # Send SIGTERM to gracefully stop
                os.kill(pid, signal.SIGTERM)
                click.echo(f"✓ Sent stop signal to agent '{name}' (PID: {pid})")
                
                # Remove from state
                del state['agents'][name]
            except ProcessLookupError:
                click.echo(f"⚠ Agent '{name}' (PID: {pid}) not found - may have already stopped")
                del state['agents'][name]
            except Exception as e:
                click.echo(f"✗ Failed to stop agent '{name}': {str(e)}", err=True)
        else:
            click.echo(f"⚠ Agent '{name}' not found in running agents")
    
    save_state(state)


@cli.command()
@click.pass_context
def status(ctx):
    """Show status of all agents."""
    state = ctx.obj['state']
    
    if not state['agents']:
        click.echo("No agents are currently running.")
        return
    
    # Header
    click.echo("\nAgent Status:")
    click.echo("-" * 50)
    click.echo(f"{'Name':<15} {'PID':<8} {'Port':<6} {'Status':<10}")
    click.echo("-" * 50)
    
    # Check each agent
    for name, info in state['agents'].items():
        pid = info['pid']
        port = info['port']
        
        # Check if process is still running
        try:
            os.kill(pid, 0)  # Signal 0 = check if process exists
            status = click.style('running', fg='green')
        except ProcessLookupError:
            status = click.style('stopped', fg='red')
            # Update state
            info['status'] = 'stopped'
        
        click.echo(f"{name:<15} {pid:<8} {port:<6} {status:<10}")
    
    click.echo("-" * 50)
    save_state(state)


@cli.command()
@click.argument('agent_name')
@click.option('--follow', '-f', is_flag=True, help='Follow log output')
@click.option('--lines', '-n', default=50, help='Number of lines to show')
def logs(agent_name: str, follow: bool, lines: int):
    """Show logs for an agent.
    
    Examples:
        agentctl logs agent1
        agentctl logs agent1 -f    # Follow logs
        agentctl logs agent1 -n 100
    """
    log_file = Path(f"logs/{agent_name}.log")
    
    if not log_file.exists():
        # Try supervisor.log as fallback
        log_file = Path("logs/supervisor.log")
        if not log_file.exists():
            click.echo(f"No log file found for agent '{agent_name}'")
            return
    
    if follow:
        # Follow mode - like tail -f
        click.echo(f"Following logs for '{agent_name}' (Ctrl+C to stop)...")
        
        try:
            # Show last N lines first
            with open(log_file, 'r') as f:
                all_lines = f.readlines()
                # Filter lines for this agent if using supervisor.log
                if log_file.name == "supervisor.log":
                    agent_lines = [l for l in all_lines if f"[{agent_name}]" in l]
                else:
                    agent_lines = all_lines
                
                for line in agent_lines[-lines:]:
                    click.echo(line.rstrip())
            
            # Then follow new lines
            with open(log_file, 'r') as f:
                # Go to end
                f.seek(0, 2)
                
                while True:
                    line = f.readline()
                    if line:
                        # Filter for agent if using supervisor.log
                        if log_file.name == "supervisor.log":
                            if f"[{agent_name}]" in line:
                                click.echo(line.rstrip())
                        else:
                            click.echo(line.rstrip())
                    else:
                        # No new line, sleep briefly
                        import time
                        time.sleep(0.1)
        
        except KeyboardInterrupt:
            click.echo("\nStopped following logs.")
    
    else:
        # Just show last N lines
        with open(log_file, 'r') as f:
            all_lines = f.readlines()
            # Filter lines for this agent if using supervisor.log
            if log_file.name == "supervisor.log":
                agent_lines = [l for l in all_lines if f"[{agent_name}]" in l]
            else:
                agent_lines = all_lines
                
            for line in agent_lines[-lines:]:
                click.echo(line.rstrip())


@cli.command()
@click.argument('from_agent')
@click.argument('to_agent')
@click.option('--bidirectional', '-b', is_flag=True, help='Create bidirectional connection')
@click.pass_context
def connect(ctx, from_agent: str, to_agent: str, bidirectional: bool):
    """Connect agents dynamically.
    
    Examples:
        agentctl connect alice bob              # One-way: alice → bob
        agentctl connect alice bob -b           # Bidirectional: alice ↔ bob
    """
    state = ctx.obj['state']
    
    # Check if agents exist
    if from_agent not in state['agents']:
        click.echo(f"✗ Agent '{from_agent}' not found", err=True)
        return
    if to_agent not in state['agents']:
        click.echo(f"✗ Agent '{to_agent}' not found", err=True)
        return
    
    # Get agent info
    from_info = state['agents'][from_agent]
    to_info = state['agents'][to_agent]
    
    # Send CONNECT command via socket
    import json
    
    async def do_connect():
        """Execute the connection via socket."""
        # Connect from_agent -> to_agent
        socket_path = f"/tmp/chaotic-af/agent-{from_agent}.sock"
        
        try:
            # Check if socket exists
            if not os.path.exists(socket_path):
                click.echo(f"✗ Agent '{from_agent}' socket not found. Is it running with socket mode?", err=True)
                return False
                
            # Connect to socket
            reader, writer = await asyncio.open_unix_connection(socket_path)
            
            # Send connect command
            cmd = {
                'cmd': 'connect',
                'target': to_agent,
                'endpoint': f'http://localhost:{to_info["port"]}/mcp'
            }
            writer.write(json.dumps(cmd).encode() + b'\n')
            await writer.drain()
            
            # Read response
            response = await reader.readline()
            result = json.loads(response.decode())
            
            writer.close()
            await writer.wait_closed()
            
            if result.get('status') == 'connected':
                click.echo(f"✓ Connected: {from_agent} → {to_agent}")
            else:
                click.echo(f"✗ Failed to connect: {result.get('error', 'Unknown error')}", err=True)
                return False
                
            # Bidirectional connection
            if bidirectional:
                # Connect to_agent -> from_agent
                socket_path = f"/tmp/chaotic-af/agent-{to_agent}.sock"
                
                if not os.path.exists(socket_path):
                    click.echo(f"✗ Agent '{to_agent}' socket not found", err=True)
                    return False
                    
                reader, writer = await asyncio.open_unix_connection(socket_path)
                
                cmd = {
                    'cmd': 'connect',
                    'target': from_agent,
                    'endpoint': f'http://localhost:{from_info["port"]}/mcp'
                }
                writer.write(json.dumps(cmd).encode() + b'\n')
                await writer.drain()
                
                response = await reader.readline()
                result = json.loads(response.decode())
                
                writer.close()
                await writer.wait_closed()
                
                if result.get('status') == 'connected':
                    click.echo(f"✓ Connected: {to_agent} → {from_agent}")
                else:
                    click.echo(f"✗ Failed reverse connection: {result.get('error', 'Unknown error')}", err=True)
                    
            return True
            
        except Exception as e:
            click.echo(f"✗ Failed to connect agents: {str(e)}", err=True)
            return False
    
    # Run the async connection
    asyncio.run(do_connect())


@cli.command()
def init():
    """Initialize a new agent configuration template."""
    
    template = """# Agent Configuration Template
agent:
  name: my_agent
  llm_provider: google        # Options: openai, anthropic, google
  llm_model: gemini-1.5-pro
  role_prompt: |
    You are a helpful assistant agent.
    Your role is to assist with various tasks.
  port: 8001

external_mcp_servers: []

logging:
  level: INFO
  file: logs/my_agent.log
"""
    
    filename = "agent_template.yaml"
    
    with open(filename, 'w') as f:
        f.write(template)
    
    click.echo(f"✓ Created agent configuration template: {filename}")
    click.echo("\nEdit this file and then run:")
    click.echo(f"  agentctl start {filename}")


def main():
    """Entry point for CLI."""
    cli(obj={})


if __name__ == '__main__':
    main()