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
    "--verbose",
    "-v",
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
                console.print(
                    f"[green]+[/green] Connected to MCP server at {server_url}"
                )

                if verbose:
                    console.print("Initialization response:", init_response)

                # If no specific operation requested, just show connection status
                console.print(
                    "Connection successful. Use 'list-resources' or 'list-tools' to explore the server."
                )

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
@click.option("--params", "-p", help="JSON string with method parameters", default="{}")
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
                    console.print(
                        f"Calling method '{method}' with params: {parsed_params}"
                    )

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
    "--name",
    "-n",
    required=True,
    help="Unique name for the server",
)
@click.option(
    "--transport",
    "-t",
    type=click.Choice(["stdio", "http"]),
    default="stdio",
    help="Transport type: 'stdio' for subprocess, 'http' for HTTP streamable",
)
@click.option(
    "--command",
    "-c",
    help="Command to execute (required for stdio transport)",
)
@click.option(
    "--args",
    "-a",
    multiple=True,
    help="Command arguments (can be specified multiple times, stdio only)",
)
@click.option(
    "--env",
    "-e",
    multiple=True,
    help="Environment variables (format: KEY=VALUE, can be specified multiple times, stdio only)",
)
@click.option(
    "--cwd",
    help="Working directory for the server (stdio only)",
)
@click.option(
    "--url",
    "-u",
    help="HTTP(S) URL for the server (required for http transport)",
)
@click.option(
    "--header",
    "-H",
    multiple=True,
    help="HTTP headers (format: KEY=VALUE, can be specified multiple times, http only)",
)
@click.option(
    "--auth-type",
    type=click.Choice(["bearer", "oauth"]),
    help="Authentication type for HTTP transport",
)
@click.option(
    "--auth-token",
    help="Authentication token for bearer auth (http only)",
)
@click.pass_context
def add(
    ctx, name, transport, command, args, env, cwd, url, header, auth_type, auth_token
):
    """
    Add a new MCP server configuration.

    Examples:
        # Add STDIO server
        mcp-open-client api add --name filesystem --command npm.cmd \\
            --args -y --args @modelcontextprotocol/server-filesystem --args .

        # Add HTTP server
        mcp-open-client api add --name remote-server --transport http \\
            --url http://example.com/mcp

        # Add HTTP server with auth
        mcp-open-client api add --name secure-server --transport http \\
            --url https://api.example.com/mcp --auth-type bearer --auth-token "token123"
    """
    api_url = ctx.obj["api_url"]
    verbose = ctx.parent.obj["verbose"]

    try:
        import json

        import requests

        # Validate transport-specific requirements
        if transport == "stdio" and not command:
            console.print(
                "[red]✗ Error:[/red] --command is required for stdio transport"
            )
            sys.exit(1)
        elif transport == "http" and not url:
            console.print("[red]✗ Error:[/red] --url is required for http transport")
            sys.exit(1)

        # Build server configuration based on transport type
        if transport == "stdio":
            # Parse environment variables
            env_dict = {}
            for e in env:
                if "=" in e:
                    key, value = e.split("=", 1)
                    env_dict[key] = value

            server_config = {
                "name": name,
                "transport": "stdio",
                "command": command,
                "args": list(args),
                "env": env_dict if env_dict else None,
                "cwd": cwd,
            }
        else:  # http
            # Parse headers
            headers_dict = {}
            for h in header:
                if "=" in h:
                    key, value = h.split("=", 1)
                    headers_dict[key] = value

            server_config = {
                "name": name,
                "transport": "http",
                "url": url,
                "headers": headers_dict if headers_dict else None,
                "auth_type": auth_type,
                "auth_token": auth_token,
            }

        request_data = {"server": server_config}

        if verbose:
            console.print(f"Adding {transport} server to API at {api_url}/servers/")
            console.print(f"Request data: {json.dumps(request_data, indent=2)}")

        response = requests.post(
            f"{api_url}/servers/",
            json=request_data,
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 201:
            data = response.json()
            console.print(
                f"[green]+[/green] Server '{name}' added successfully ({transport} transport)"
            )
            console.print(f"Server ID: {data['server']['id']}")
            console.print(f"Status: {data['server']['status']}")
        else:
            console.print(f"[red]x Failed to add server:[/red] {response.text}")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]x Error adding server:[/red] {e}")
        sys.exit(1)


@api.command()
@click.option(
    "--format",
    "-f",
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
                    "error": "red",
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
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 200:
            data = response.json()
            console.print(
                f"[green]+[/green] Server '{data['server']['config']['name']}' started successfully"
            )
            console.print(f"Status: {data['server']['status']}")
            if data["server"].get("process_id"):
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
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 200:
            data = response.json()
            console.print(
                f"[green]+[/green] Server '{data['server']['config']['name']}' stopped successfully"
            )
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
    "--format",
    "-f",
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
    "--port",
    "-p",
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


# AI Provider Management Commands
@api.group()
@click.pass_context
def providers(ctx):
    """
    Manage AI providers through the REST API.

    These commands interact with the MCP Open Client API to configure and manage AI providers.
    """
    pass


@providers.command()
@click.option(
    "--name",
    "-n",
    required=True,
    help="Name of the AI provider (e.g., OpenAI, Anthropic, Cerebras)",
)
@click.option(
    "--type",
    "-t",
    required=True,
    type=click.Choice(["openai", "anthropic", "cerebras", "openrouter", "custom"]),
    help="Type of the AI provider",
)
@click.option(
    "--base-url",
    "-u",
    required=True,
    help="Base URL for the provider API",
)
@click.option(
    "--api-key",
    "-k",
    help="API key for the provider (can be set later)",
)
@click.pass_context
def add(ctx, name, type, base_url, api_key):
    """
    Add a new AI provider configuration.
    
    Example:
        mcp-open-client api providers add --name "OpenAI" --type openai \\
            --base-url "https://api.openai.com/v1" --api-key "sk-..."
    """
    api_url = ctx.parent.obj["api_url"]
    verbose = ctx.parent.parent.obj["verbose"]

    try:
        import json

        import requests

        # Build provider configuration
        provider_config = {
            "name": name,
            "provider_type": type,
            "base_url": base_url,
            "api_key": api_key,
            "enabled": True,
            "models": {"small": None, "main": None},
        }

        request_data = {"provider": provider_config}

        if verbose:
            console.print(f"Adding provider to API at {api_url}/providers/")
            console.print(f"Request data: {json.dumps(request_data, indent=2)}")

        response = requests.post(
            f"{api_url}/providers/",
            json=request_data,
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 201:
            data = response.json()
            console.print(f"[green]+[/green] Provider '{name}' added successfully")
            console.print(f"Provider ID: {data['provider']['id']}")
            console.print(f"Type: {data['provider']['provider_type']}")
        else:
            console.print(f"[red]X Failed to add provider:[/red] {response.text}")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]X Error adding provider:[/red] {e}")
        sys.exit(1)


@providers.command()
@click.option(
    "--format",
    "-f",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format",
)
@click.pass_context
def list(ctx, format):
    """
    List all configured AI providers.
    """
    api_url = ctx.parent.obj["api_url"]

    try:
        import json

        import requests
        from rich.table import Table

        response = requests.get(f"{api_url}/providers/")

        if response.status_code != 200:
            console.print(f"[red]X Failed to list providers:[/red] {response.text}")
            sys.exit(1)

        data = response.json()
        providers = data["providers"]

        if format == "json":
            console.print(json.dumps(data, indent=2))
        else:
            if not providers:
                console.print("[yellow]No providers configured[/yellow]")
                return

            table = Table(title="AI Providers")
            table.add_column("ID", style="cyan", no_wrap=True)
            table.add_column("Name", style="magenta")
            table.add_column("Type", style="green")
            table.add_column("Base URL", style="blue")
            table.add_column("Enabled", style="yellow")
            table.add_column("Default", style="red")

            for provider in providers:
                enabled_status = (
                    "[green]+[/green]" if provider["enabled"] else "[red]-[/red]"
                )
                default_status = (
                    "[green]+[/green]"
                    if data.get("default_provider") == provider["id"]
                    else "[red]-[/red]"
                )

                table.add_row(
                    provider["id"][:8] + "...",
                    provider["config"]["name"],
                    provider["config"].get("provider_type", "unknown"),
                    (
                        provider["config"]["base_url"][:40] + "..."
                        if len(provider["config"]["base_url"]) > 40
                        else provider["config"]["base_url"]
                    ),
                    enabled_status,
                    default_status,
                )

            console.print(table)
            console.print(f"\nTotal: {data['count']} providers")

    except Exception as e:
        console.print(f"[red]X Error listing providers:[/red] {e}")
        sys.exit(1)


@providers.command()
@click.argument("provider_id")
@click.pass_context
def show(ctx, provider_id):
    """
    Show detailed information about a specific AI provider.

    PROVIDER_ID: ID of the provider to show
    """
    api_url = ctx.parent.obj["api_url"]

    try:
        import json

        import requests

        response = requests.get(f"{api_url}/providers/{provider_id}")

        if response.status_code != 200:
            console.print(f"[red]X Failed to get provider:[/red] {response.text}")
            sys.exit(1)

        data = response.json()
        provider = data["provider"]
        config = provider["config"]

        console.print(f"[bold]Provider Details:[/bold]")
        console.print(f"ID: {provider['id']}")
        console.print(f"Name: {config['name']}")
        console.print(f"Type: {config.get('provider_type', 'unknown')}")
        console.print(f"Base URL: {config['base_url']}")
        console.print(
            f"Enabled: {'[green]+[/green]' if provider['enabled'] else '[red]-[/red]'}"
        )

        models = config.get("models", {})
        if models.get("small"):
            console.print(f"\n[bold]Small Model:[/bold]")
            console.print(f"Name: {models['small'].get('model_name', 'N/A')}")
            console.print(f"Max Tokens: {models['small'].get('max_tokens', 'N/A')}")

        if models.get("main"):
            console.print(f"\n[bold]Main Model:[/bold]")
            console.print(f"Name: {models['main'].get('model_name', 'N/A')}")
            console.print(f"Max Tokens: {models['main'].get('max_tokens', 'N/A')}")

    except Exception as e:
        console.print(f"[red]X Error getting provider:[/red] {e}")
        sys.exit(1)


@providers.command()
@click.argument("provider_id")
@click.option(
    "--name",
    "-n",
    help="New name for the provider",
)
@click.option(
    "--base-url",
    "-u",
    help="New base URL for the provider",
)
@click.option(
    "--api-key",
    "-k",
    help="New API key for the provider",
)
@click.pass_context
def update(ctx, provider_id, name, base_url, api_key):
    """
    Update an AI provider configuration.

    PROVIDER_ID: ID of the provider to update
    """
    api_url = ctx.parent.obj["api_url"]
    verbose = ctx.parent.parent.obj["verbose"]

    try:
        import json

        import requests

        # Build update data with only provided fields
        update_data = {}
        if name:
            update_data["name"] = name
        if base_url:
            update_data["base_url"] = base_url
        if api_key:
            update_data["api_key"] = api_key

        if not update_data:
            console.print("[yellow]No updates provided[/yellow]")
            return

        if verbose:
            console.print(f"Updating provider {provider_id}...")
            console.print(f"Update data: {json.dumps(update_data, indent=2)}")

        response = requests.patch(
            f"{api_url}/providers/{provider_id}",
            json=update_data,
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 200:
            data = response.json()
            console.print(f"[green]+[/green] Provider updated successfully")
            console.print(f"Name: {data['provider']['name']}")
        else:
            console.print(f"[red]✗ Failed to update provider:[/red] {response.text}")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]✗ Error updating provider:[/red] {e}")
        sys.exit(1)


@providers.command()
@click.argument("provider_id")
@click.pass_context
def delete(ctx, provider_id):
    """
    Delete an AI provider configuration.

    PROVIDER_ID: ID of the provider to delete
    """
    api_url = ctx.parent.obj["api_url"]

    try:
        import requests

        # Confirm before deletion
        if not click.confirm(
            f"Are you sure you want to delete provider '{provider_id}'?"
        ):
            console.print("[yellow]Operation cancelled[/yellow]")
            return

        response = requests.delete(f"{api_url}/providers/{provider_id}")

        if response.status_code == 200:
            console.print(
                f"[green]+[/green] Provider '{provider_id}' deleted successfully"
            )
        else:
            console.print(f"[red]✗ Failed to delete provider:[/red] {response.text}")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]✗ Error deleting provider:[/red] {e}")
        sys.exit(1)


# Model management commands
@providers.group()
def models():
    """
    Manage AI models for providers.
    """
    pass


@models.command()
@click.argument("provider_id")
@click.argument("model_type", type=click.Choice(["small", "main"]))
@click.option(
    "--name",
    "-n",
    required=True,
    help="Model name (e.g., gpt-3.5-turbo, claude-3-haiku)",
)
@click.option(
    "--max-tokens",
    "-m",
    type=int,
    help="Maximum tokens for this model",
)
@click.pass_context
def set(ctx, provider_id, model_type, name, max_tokens):
    """
    Set a small or main model for a provider.

    PROVIDER_ID: ID of the provider
    MODEL_TYPE: Type of model (small or main)

    Example:
        mcp-open-client api providers models set <provider_id> small --name "gpt-3.5-turbo" --max-tokens 4096
    """
    api_url = ctx.parent.parent.obj["api_url"]

    try:
        import json

        import requests

        model_config = {"name": name, "max_tokens": max_tokens}

        response = requests.post(
            f"{api_url}/providers/{provider_id}/models/{model_type}",
            json=model_config,
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 201:
            data = response.json()
            console.print(
                f"[green]+[/green] {model_type.capitalize()} model set successfully"
            )
            console.print(f"Model: {data['model_config']['name']}")
        else:
            console.print(f"[red]✗ Failed to set model:[/red] {response.text}")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]✗ Error setting model:[/red] {e}")
        sys.exit(1)


@models.command()
@click.argument("provider_id")
@click.pass_context
def list(ctx, provider_id):
    """
    List models configured for a provider.

    PROVIDER_ID: ID of the provider
    """
    api_url = ctx.parent.parent.obj["api_url"]

    try:
        import json

        import requests
        from rich.table import Table

        response = requests.get(f"{api_url}/providers/{provider_id}/models")

        if response.status_code != 200:
            console.print(f"[red]✗ Failed to get models:[/red] {response.text}")
            sys.exit(1)

        data = response.json()
        models = data.get("models", {})

        if not models.get("small") and not models.get("main"):
            console.print("[yellow]No models configured for this provider[/yellow]")
            return

        table = Table(title=f"Models for Provider {provider_id[:8]}...")
        table.add_column("Type", style="cyan")
        table.add_column("Name", style="magenta")
        table.add_column("Max Tokens", style="green")

        if models.get("small"):
            table.add_row(
                "small",
                models["small"]["model_name"],
                str(models["small"].get("max_tokens", "N/A")),
            )

        if models.get("main"):
            table.add_row(
                "main",
                models["main"]["model_name"],
                str(models["main"].get("max_tokens", "N/A")),
            )

        console.print(table)

    except Exception as e:
        console.print(f"[red]✗ Error listing models:[/red] {e}")
        sys.exit(1)


@models.command()
@click.argument("provider_id")
@click.argument("model_type", type=click.Choice(["small", "main"]))
@click.pass_context
def remove(ctx, provider_id, model_type):
    """
    Remove a model configuration from a provider.

    PROVIDER_ID: ID of the provider
    MODEL_TYPE: Type of model to remove (small or main)
    """
    api_url = ctx.parent.parent.obj["api_url"]

    try:
        import requests

        if not click.confirm(
            f"Are you sure you want to remove the {model_type} model from provider '{provider_id}'?"
        ):
            console.print("[yellow]Operation cancelled[/yellow]")
            return

        response = requests.delete(
            f"{api_url}/providers/{provider_id}/models/{model_type}"
        )

        if response.status_code == 200:
            console.print(
                f"[green]+[/green] {model_type.capitalize()} model removed successfully"
            )
        else:
            console.print(f"[red]✗ Failed to remove model:[/red] {response.text}")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]✗ Error removing model:[/red] {e}")
        sys.exit(1)


# Provider control commands
@providers.command()
@click.argument("provider_id")
@click.pass_context
def enable(ctx, provider_id):
    """
    Enable an AI provider.

    PROVIDER_ID: ID of the provider to enable
    """
    api_url = ctx.parent.obj["api_url"]

    try:
        import requests

        response = requests.post(f"{api_url}/providers/{provider_id}/enable")

        if response.status_code == 200:
            console.print(
                f"[green]+[/green] Provider '{provider_id}' enabled successfully"
            )
        else:
            console.print(f"[red]✗ Failed to enable provider:[/red] {response.text}")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]✗ Error enabling provider:[/red] {e}")
        sys.exit(1)


@providers.command()
@click.argument("provider_id")
@click.pass_context
def disable(ctx, provider_id):
    """
    Disable an AI provider.

    PROVIDER_ID: ID of the provider to disable
    """
    api_url = ctx.parent.obj["api_url"]

    try:
        import requests

        response = requests.post(f"{api_url}/providers/{provider_id}/disable")

        if response.status_code == 200:
            console.print(
                f"[green]+[/green] Provider '{provider_id}' disabled successfully"
            )
        else:
            console.print(f"[red]✗ Failed to disable provider:[/red] {response.text}")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]✗ Error disabling provider:[/red] {e}")
        sys.exit(1)


@providers.command()
@click.argument("provider_id")
@click.pass_context
def set_default(ctx, provider_id):
    """
    Set an AI provider as the default.

    PROVIDER_ID: ID of the provider to set as default
    """
    api_url = ctx.parent.obj["api_url"]

    try:
        import requests

        response = requests.post(f"{api_url}/providers/{provider_id}/set-default")

        if response.status_code == 200:
            console.print(
                f"[green]+[/green] Provider '{provider_id}' set as default successfully"
            )
        else:
            console.print(
                f"[red]✗ Failed to set default provider:[/red] {response.text}"
            )
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]✗ Error setting default provider:[/red] {e}")
        sys.exit(1)


@providers.command()
@click.pass_context
def default(ctx):
    """
    Show the current default AI provider.
    """
    api_url = ctx.parent.obj["api_url"]

    try:
        import requests

        response = requests.get(f"{api_url}/providers/default/current")

        if response.status_code == 200:
            data = response.json()
            if data.get("default_provider"):
                provider = data["default_provider"]
                console.print(f"[bold]Default Provider:[/bold]")
                console.print(f"ID: {provider['id']}")
                console.print(f"Name: {provider['name']}")
                console.print(
                    f"Enabled: {'[green]+[/green]' if provider['enabled'] else '[red]-[/red]'}"
                )
            else:
                console.print("[yellow]No default provider set[/yellow]")
        else:
            console.print(
                f"[red]X Failed to get default provider:[/red] {response.text}"
            )
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]X Error getting default provider:[/red] {e}")
        sys.exit(1)


@providers.command()
@click.argument("provider_id")
@click.option(
    "--model-name",
    "-m",
    help="Specific model to test (optional)",
)
@click.pass_context
def test(ctx, provider_id, model_name):
    """
    Test an AI provider connection.

    PROVIDER_ID: ID of the provider to test
    """
    api_url = ctx.parent.obj["api_url"]

    try:
        import requests

        test_data = {"model_name": model_name} if model_name else {}

        response = requests.post(
            f"{api_url}/providers/{provider_id}/test",
            json=test_data,
            headers={"Content-Type": "application/json"},
        )

        if response.status_code == 200:
            data = response.json()
            if data["success"]:
                console.print(f"[green]+[/green] Provider test successful")
                console.print(f"Response time: {data.get('response_time_ms', 'N/A')}ms")
                if data.get("available_models"):
                    console.print(
                        f"Available models: {', '.join(data['available_models'][:5])}"
                    )
                    if len(data["available_models"]) > 5:
                        console.print(
                            f"and {len(data['available_models']) - 5} more..."
                        )
            else:
                console.print(
                    f"[red]✗ Provider test failed:[/red] {data.get('error_message', 'Unknown error')}"
                )
        else:
            console.print(f"[red]✗ Failed to test provider:[/red] {response.text}")
            sys.exit(1)

    except Exception as e:
        console.print(f"[red]✗ Error testing provider:[/red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    cli()
