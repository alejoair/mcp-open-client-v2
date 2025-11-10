"""
Tests for the MCP Client.
"""

import pytest
from unittest.mock import AsyncMock, patch

from mcp_open_client import MCPClient
from mcp_open_client.exceptions import ConnectionError, ProtocolError


@pytest.mark.asyncio
async def test_client_initialization():
    """Test that the client initializes correctly."""
    client = MCPClient("http://localhost:8080", timeout=10.0)
    
    assert client.server_url == "http://localhost:8080"
    assert client.timeout == 10.0
    assert not client.is_connected


@pytest.mark.asyncio
async def test_client_connect():
    """Test client connection."""
    client = MCPClient("http://localhost:8080")
    
    await client.connect()
    assert client.is_connected
    
    await client.disconnect()
    assert not client.is_connected


@pytest.mark.asyncio
async def test_client_context_manager():
    """Test the async context manager functionality."""
    client = MCPClient("http://localhost:8080")
    
    async with client:
        assert client.is_connected
    
    assert not client.is_connected


@pytest.mark.asyncio
async def test_send_request():
    """Test sending requests to the server."""
    client = MCPClient("http://localhost:8080")
    
    async with client:
        await client.initialize()
        
        response = await client.send_request("test/method", {"param": "value"})
        
        # Since we're using mock implementation, check that we get a response
        assert "result" in response
        assert "test/method" in response["result"]


@pytest.mark.asyncio
async def test_send_request_not_connected():
    """Test that sending a request when not connected raises an error."""
    client = MCPClient("http://localhost:8080")
    
    with pytest.raises(ConnectionError):
        await client.send_request("test/method")


@pytest.mark.asyncio
async def test_initialize():
    """Test the initialize method."""
    client = MCPClient("http://localhost:8080")
    
    async with client:
        response = await client.initialize()
        
        assert "result" in response


@pytest.mark.asyncio
async def test_list_resources():
    """Test listing resources."""
    client = MCPClient("http://localhost:8080")
    
    async with client:
        await client.initialize()
        resources = await client.list_resources()
        
        assert "result" in resources


@pytest.mark.asyncio
async def test_list_tools():
    """Test listing tools."""
    client = MCPClient("http://localhost:8080")
    
    async with client:
        await client.initialize()
        tools = await client.list_tools()
        
        assert "result" in tools