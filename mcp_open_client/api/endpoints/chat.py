"""
API endpoints for OpenAI-compatible chat with tool calling support.
"""

import json
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request

from mcp_open_client.api.models.chat import (
    ChatRequest,
    ChatResponse,
    ErrorResponse,
    ModelType,
)
from mcp_open_client.core.chat_service import ChatService

router = APIRouter(prefix="/v1", tags=["chat"])


def get_chat_service() -> ChatService:
    """Get chat service instance."""
    return ChatService()


@router.post(
    "/chat/completions",
    response_model=ChatResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
    },
    operation_id="chat_completion",
)
async def create_chat_completion(
    request: ChatRequest, chat_service: ChatService = Depends(get_chat_service)
):
    """
    Create a chat completion.

    This endpoint is compatible with OpenAI's chat completions API but integrates
    with our provider system and automatically includes tools from running MCP servers.

    The endpoint supports:
    - model_type: "small" or "main" to select the appropriate model
    - Automatic tool calling using tools from running MCP servers
    - All standard OpenAI parameters
    - Provider override through request parameters
    """
    try:
        response = chat_service.chat_completion(request)
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": {"message": str(e), "type": "invalid_request_error"}},
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": f"Internal server error: {str(e)}",
                    "type": "internal_error",
                }
            },
        )


@router.post("/chat/stream", tags=["chat"], operation_id="chat_stream")
async def stream_chat_completion(
    request: ChatRequest, chat_service: ChatService = Depends(get_chat_service)
):
    """
    Stream a chat completion.

    This endpoint provides streaming responses compatible with OpenAI's streaming API.
    """
    try:
        # Validate that streaming is requested
        if not request.stream:
            # If stream=False, redirect to regular chat completion
            response = chat_service.chat_completion(request)
            return response

        # Return streaming response
        return await stream_response(chat_service, request)

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail={"error": {"message": str(e), "type": "invalid_request_error"}},
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": f"Internal server error: {str(e)}",
                    "type": "internal_error",
                }
            },
        )


async def stream_response(chat_service: ChatService, request: ChatRequest):
    """
    Handle streaming chat completion response.
    """
    import asyncio

    async def generate():
        try:
            stream = chat_service.stream_chat_completion(request)
            async for chunk in stream:
                # Convert OpenAI chunk to our format and yield
                yield f"data: {json.dumps(chunk.model_dump() if hasattr(chunk, 'model_dump') else chunk, default=str)}\n\n"
            yield "data: [DONE]\n\n"
        except Exception as e:
            error_data = {"error": {"message": str(e), "type": "internal_error"}}
            yield f"data: {json.dumps(error_data)}\n\n"

    return generate()


@router.get("/models", tags=["models"], operation_id="chat_list_models")
async def list_models(chat_service: ChatService = Depends(get_chat_service)):
    """
    List available models for the default provider.
    """
    try:
        from mcp_open_client.core.providers import AIProviderManager

        provider_manager = AIProviderManager()

        # Get default provider
        default_provider = provider_manager.get_default_provider()
        if not default_provider:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "message": "No default provider configured",
                        "type": "invalid_request_error",
                    }
                },
            )

        provider_config = provider_manager.get_provider(default_provider)
        if not provider_config:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": {
                        "message": f"Default provider '{default_provider}' not found",
                        "type": "invalid_request_error",
                    }
                },
            )

        # Build model list
        models = []

        # Add small model if available
        if provider_config.models.small:
            models.append(
                {
                    "id": provider_config.models.small.name,
                    "object": "model",
                    "created": 1677610602,
                    "owned_by": default_provider,
                }
            )

        # Add main model if available
        if provider_config.models.main:
            models.append(
                {
                    "id": provider_config.models.main.name,
                    "object": "model",
                    "created": 1677610602,
                    "owned_by": default_provider,
                }
            )

        # Add generic models based on request model
        if request.model:
            models.append(
                {
                    "id": request.model,
                    "object": "model",
                    "created": 1677610602,
                    "owned_by": default_provider,
                }
            )

        return {"object": "list", "data": models}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": f"Failed to list models: {str(e)}",
                    "type": "internal_error",
                }
            },
        )


@router.get("/health", tags=["system"], operation_id="chat_health_check")
async def health_check():
    """
    Health check endpoint for the chat service.
    """
    try:
        # Check if we can access provider manager
        from mcp_open_client.core.providers import AIProviderManager

        provider_manager = AIProviderManager()
        providers = provider_manager.list_providers()

        # Check if we can access server manager
        from mcp_open_client.core.server_manager import MCPServerManager

        server_manager = MCPServerManager()
        servers = server_manager.list_servers()

        # Count running servers
        running_servers = [s for s in servers if s.status.value == "running"]

        return {
            "status": "healthy",
            "providers": len(providers),
            "servers": len(servers),
            "running_servers": len(running_servers),
        }

    except Exception as e:
        raise HTTPException(
            status_code=503, detail={"status": "unhealthy", "error": str(e)}
        )


@router.get("/tools", tags=["tools"], operation_id="chat_list_tools")
async def list_available_tools(
    server_names: Optional[str] = None,
    chat_service: ChatService = Depends(get_chat_service),
):
    """
    List available tools from MCP servers.

    Args:
        server_names: Comma-separated list of server names to get tools from.
                     If not provided, gets tools from all running servers.
    """
    try:
        # Parse server names if provided
        target_servers = None
        if server_names:
            target_servers = [name.strip() for name in server_names.split(",")]

        # Get tools from MCP servers
        tools = chat_service._get_mcp_tools(target_servers)

        return {"object": "list", "data": tools, "count": len(tools)}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={
                "error": {
                    "message": f"Failed to list tools: {str(e)}",
                    "type": "internal_error",
                }
            },
        )
