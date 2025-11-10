"""
CLI interface for MCP Open Client API.
"""

import click
from .main import start_server


@click.command()
@click.option(
    "--host",
    default="127.0.0.1",
    help="Host to bind the server to (default: 127.0.0.1)",
)
@click.option(
    "--port",
    type=int,
    default=8000,
    help="Port to bind the server to (default: 8000)",
)
@click.option(
    "--reload",
    is_flag=True,
    help="Enable auto-reload for development",
)
def main(host: str, port: int, reload: bool):
    """Start the MCP Open Client API server."""
    click.echo(f"Starting MCP Open Client API on http://{host}:{port}")
    click.echo(f"Documentation available at http://{host}:{port}/docs")
    start_server(host=host, port=port, reload=reload)


if __name__ == "__main__":
    main()