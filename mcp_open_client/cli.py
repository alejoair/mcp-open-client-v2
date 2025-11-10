"""
Command-line interface for MCP Open Client using Click.
"""

import asyncio
import sys
from typing import Optional

import click
from rich.console import Console

from .client import MCPClient
from .exceptions import MCPError

console = Console()


@click.group()
@click.option(
    "--timeout",
    type=float,
    default=30.0,
    help="Connection and request timeout in seconds (default: 30.0)",
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    help="Enable verbose output",
)
@click.pass_context
def cli(ctx, timeout, verbose):
    """
    MCP Open Client - A client for the Model Context Protocol.
    
    Connect to MCP servers and interact with their resources and tools.
    """
    ctx.ensure_object(dict)
    ctx.obj["timeout"] = timeout
    ctx.obj["verbose"] = verbose


@cli.command()
@click.argument("server_url")
@click.pass_context
def connect(ctx, server_url):
    """
    Connect to an MCP server and test the connection.
    
    SERVER_URL: URL of the MCP server to connect to (e.g., http://localhost:8080)
    """
    timeout = ctx.obj["timeout"]
    verbose = ctx.obj["verbose"]
    
    if verbose:
        console.print(f"Connecting to {server_url} with timeout {timeout}s...")
    
    try:
        client = MCPClient(server_url, timeout)
        
        async def _connect():
            async with client:
                if verbose:
                    console.print("Initializing session...")
                
                # Initialize the connection
                init_response = await client.initialize()
                console.print(f"[green]+[/green] Connected to MCP server at {server_url}")
                
                if verbose:
                    console.print("Initialization response:", init_response)
                
                # If no specific operation requested, just show connection status
                console.print("Connection successful. Use 'list-resources' or 'list-tools' to explore the server.")
        
        asyncio.run(_connect())
        
    except MCPError as e:
        console.print(f"[red]✗ MCP Error:[/red] {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]x[/red] Unexpected error: {e}")
        sys.exit(1)


@cli.command()
@click.argument("server_url")
@click.pass_context
def list_resources(ctx, server_url):
    """
    List available resources from an MCP server.
    
    SERVER_URL: URL of the MCP server to connect to
    """
    timeout = ctx.obj["timeout"]
    verbose = ctx.obj["verbose"]
    
    try:
        client = MCPClient(server_url, timeout)
        
        async def _list_resources():
            async with client:
                if verbose:
                    console.print("Initializing session...")
                
                await client.initialize()
                
                if verbose:
                    console.print("Fetching resources...")
                
                resources = await client.list_resources()
                
                console.print("[bold]Available resources:[/bold]")
                console.print(resources)
        
        asyncio.run(_list_resources())
        
    except MCPError as e:
        console.print(f"[red]x[/red] Error listing resources: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗ Unexpected error:[/red] {e}")
        sys.exit(1)


@cli.command()
@click.argument("server_url")
@click.pass_context
def list_tools(ctx, server_url):
    """
    List available tools from an MCP server.
    
    SERVER_URL: URL of the MCP server to connect to
    """
    timeout = ctx.obj["timeout"]
    verbose = ctx.obj["verbose"]
    
    try:
        client = MCPClient(server_url, timeout)
        
        async def _list_tools():
            async with client:
                if verbose:
                    console.print("Initializing session...")
                
                await client.initialize()
                
                if verbose:
                    console.print("Fetching tools...")
                
                tools = await client.list_tools()
                
                console.print("[bold]Available tools:[/bold]")
                console.print(tools)
        
        asyncio.run(_list_tools())
        
    except MCPError as e:
        console.print(f"[red]x[/red] Error listing tools: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]x[/red] Unexpected error: {e}")
        sys.exit(1)


@cli.command()
@click.argument("server_url")
@click.argument("method")
@click.option(
    "--params", "-p",
    help="JSON string with method parameters",
    default="{}"
)
@click.pass_context
def call(ctx, server_url, method, params):
    """
    Call a custom method on an MCP server.
    
    SERVER_URL: URL of the MCP server to connect to
    METHOD: MCP method to call
    """
    timeout = ctx.obj["timeout"]
    verbose = ctx.obj["verbose"]
    
    try:
        import json
        
        # Parse params if provided
        parsed_params = {}
        if params and params != "{}":
            try:
                parsed_params = json.loads(params)
            except json.JSONDecodeError:
                console.print(f"[red]x[/red] Invalid JSON in params: {params}")
                sys.exit(1)
        
        client = MCPClient(server_url, timeout)
        
        async def _call():
            async with client:
                if verbose:
                    console.print("Initializing session...")
                
                await client.initialize()
                
                if verbose:
                    console.print(f"Calling method '{method}' with params: {parsed_params}")
                
                response = await client.send_request(method, parsed_params)
                
                console.print(f"[bold]Response for {method}:[/bold]")
                console.print(response)
        
        asyncio.run(_call())
        
    except MCPError as e:
        console.print(f"[red]✗ Error calling method:[/red] {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]✗ Unexpected error:[/red] {e}")
        sys.exit(1)


# API Server Management Commands
@cli.group()
@click.option(
    "--api-url",
    default="http://localhost:8001",
    help="URL of the MCP Open Client API (default: http://localhost:8001)",
)
@click.pass_context
def api(ctx, api_url):
    """
    Manage MCP servers through the REST API.
    
    These commands interact with the MCP Open Client API to start, stop, and manage MCP servers.
    """
    ctx.ensure_object(dict)
    ctx.obj["api_url"] = api_url.rstrip("/")


@api.command()
@click.option(
    "--name", "-n",
    required=True,
    help="Unique name for the server",
)
@click.option(
    "--command", "-c",
    required=True,
    help="Command to execute for the server",
)
@click.option(
    "--args", "-a",
    multiple=True,
    help="Command arguments (can be specified multiple times)",
)
@click.option(
    "--env", "-e",
    multiple=True,
    help="Environment variables (format: KEY=VALUE, can be specified multiple times)",
)
@click.option(
    "--cwd",
    help="Working directory for the server",
)
@click.pass_context
def add(ctx, name, command, args, env, cwd):
    """
    Add a new MCP server configuration.
    
    Example:
        mcp-open-client api add --name filesystem --command npm.cmd \\
            --args -x --args -y --args @modelcontextprotocol/server-filesystem --args .
    """
    api_url = ctx.obj["api_url"]
    verbose = ctx.parent.obj["verbose"]
    
    try:
        import json
        import requests
        
        # Parse environment variables
        env_dict = {}
        for e in env:
            if "=" in e:
                key, value = e.split("=", 1)
                env_dict[key] = value
        
        # Build server configuration
        server_config = {
            "name": name,
            "transport": "stdio",
            "command": command,
            "args": list(args),
            "env": env_dict if env_dict else None,
            "cwd": cwd
        }
        
        request_data = {"server": server_config}
        
        if verbose:
            console.print(f"Adding server to API at {api_url}/servers/")
            console.print(f"Request data: {json.dumps(request_data, indent=2)}")
        
        response = requests.post(
            f"{api_url}/servers/",
            json=request_data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 201:
            data = response.json()
            console.print(f"[green]+[/green] Server '{name}' added successfully")
            console.print(f"Server ID: {data['server']['id']}")
            console.print(f"Status: {data['server']['status']}")
        else:
            console.print(f"[red]✗ Failed to add server:[/red] {response.text}")
            sys.exit(1)
            
    except Exception as e:
        console.print(f"[red]✗ Error adding server:[/red] {e}")
        sys.exit(1)


@api.command()
@click.option(
    "--format", "-f",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
@click.pass_context
def list(ctx, format):
    """
    List all configured MCP servers.
    """
    api_url = ctx.obj["api_url"]
    
    try:
        import json
        import requests
        from rich.table import Table
        
        response = requests.get(f"{api_url}/servers/")
        
        if response.status_code != 200:
            console.print(f"[red]✗ Failed to list servers:[/red] {response.text}")
            sys.exit(1)
        
        data = response.json()
        servers = data["servers"]
        
        if format == "json":
            console.print(json.dumps(data, indent=2))
        else:
            if not servers:
                console.print("[yellow]No servers configured[/yellow]")
                return
            
            table = Table(title="MCP Servers")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Name", style="magenta")
            table.add_column("Command", style="green")
            table.add_column("Status", style="yellow")
            table.add_column("Created", style="blue")
            
            for server in servers:
                status_color = {
                    "configured": "white",
                    "starting": "yellow",
                    "running": "green",
                    "stopping": "orange3",
                    "stopped": "red",
                    "error": "red"
                }.get(server["status"], "white")
                
                table.add_row(
                    server["id"][:8] + "...",
                    server["config"]["name"],
                    server["config"]["command"],
                    f"[{status_color}]{server['status']}[/{status_color}]",
                    server["created_at"][:19] + "Z",
                )
            
            console.print(table)
            console.print(f"\nTotal: {data['count']} servers")
            
    except Exception as e:
        console.print(f"[red]✗ Error listing servers:[/red] {e}")
        sys.exit(1)


@api.command()
@click.argument("server_id")
@click.pass_context
def start(ctx, server_id):
    """
    Start a configured MCP server.
    
    SERVER_ID: ID of the server to start
    """
    api_url = ctx.obj["api_url"]
    verbose = ctx.parent.obj["verbose"]
    
    try:
        import requests
        
        if verbose:
            console.print(f"Starting server {server_id}...")
        
        response = requests.post(
            f"{api_url}/servers/{server_id}/start",
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            console.print(f"[green]+[/green] Server '{data['server']['config']['name']}' started successfully")
            console.print(f"Status: {data['server']['status']}")
            if data['server'].get('process_id'):
                console.print(f"Process ID: {data['server']['process_id']}")
        else:
            console.print(f"[red]✗ Failed to start server:[/red] {response.text}")
            sys.exit(1)
            
    except Exception as e:
        console.print(f"[red]✗ Error starting server:[/red] {e}")
        sys.exit(1)


@api.command()
@click.argument("server_id")
@click.pass_context
def stop(ctx, server_id):
    """
    Stop a running MCP server.
    
    SERVER_ID: ID of the server to stop
    """
    api_url = ctx.obj["api_url"]
    verbose = ctx.parent.obj["verbose"]
    
    try:
        import requests
        
        if verbose:
            console.print(f"Stopping server {server_id}...")
        
        response = requests.post(
            f"{api_url}/servers/{server_id}/stop",
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            data = response.json()
            console.print(f"[green]+[/green] Server '{data['server']['config']['name']}' stopped successfully")
            console.print(f"Status: {data['server']['status']}")
        else:
            console.print(f"[red]✗ Failed to stop server:[/red] {response.text}")
            sys.exit(1)
            
    except Exception as e:
        console.print(f"[red]✗ Error stopping server:[/red] {e}")
        sys.exit(1)


@api.command()
@click.argument("server_id")
@click.option(
    "--format", "-f",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
@click.pass_context
def tools(ctx, server_id, format):
    """
    List tools available from a running MCP server.
    
    SERVER_ID: ID of the server to get tools from
    """
    api_url = ctx.obj["api_url"]
    
    try:
        import json
        import requests
        from rich.table import Table
        
        response = requests.get(f"{api_url}/servers/{server_id}/tools")
        
        if response.status_code != 200:
            console.print(f"[red]✗ Failed to get tools:[/red] {response.text}")
            sys.exit(1)
        
        data = response.json()
        
        if format == "json":
            console.print(json.dumps(data, indent=2))
        else:
            console.print(f"[bold]Tools from '{data['server_name']}':[/bold]")
            console.print(f"Status: {data['status']}")
            console.print(f"Message: {data['message']}\n")
            
            if not data["tools"]:
                console.print("[yellow]No tools available[/yellow]")
                return
            
            table = Table()
            table.add_column("Tool Name", style="cyan", no_wrap=True)
            table.add_column("Description", style="white")
            
            for tool in data["tools"]:
                description = tool.get("description", "No description")[:80]
                if len(tool.get("description", "")) > 80:
                    description += "..."
                table.add_row(tool["name"], description)
            
            console.print(table)
            console.print(f"\nTotal: {len(data['tools'])} tools")
            
    except Exception as e:
        console.print(f"[red]✗ Error getting tools:[/red] {e}")
        sys.exit(1)


@api.command("serve")
@click.option(
    "--port", "-p",
    type=int,
    default=8001,
    help="Port to run the API server on (default: 8001)",
)
@click.option(
    "--host",
    default="127.0.0.1",
    help="Host to bind the API server to (default: 127.0.0.1)",
)
@click.pass_context
def serve(ctx, port, host):
    """
    Start the MCP Open Client API server.
    
    This starts the REST API server that manages MCP servers.
    """
    try:
        from .api.main import start_server
        
        console.print(f"Starting MCP Open Client API server on {host}:{port}")
        console.print("Press Ctrl+C to stop the server")
        
        import uvicorn
        uvicorn.run("mcp_open_client.api.main:app", host=host, port=port, reload=False)
        
    except KeyboardInterrupt:
        console.print("\n[yellow]Server stopped by user[/yellow]")
    except Exception as e:
        console.print(f"[red]✗ Error starting server:[/red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli()