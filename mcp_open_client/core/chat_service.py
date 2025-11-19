"""
Chat service for handling OpenAI-compatible chat requests with provider integration.
"""

import json
import time
import uuid
from typing import Any, Dict, List, Optional, Union

from openai import OpenAI

from mcp_open_client.api.models.chat import (
    ChatRequest,
    ChatResponse,
    Choice,
    Message,
    ModelType,
    ToolCall,
    Usage,
)
from mcp_open_client.api.models.server import ToolInfo
from mcp_open_client.core.providers import AIProviderManager


class ChatService:
    """Service for handling chat completions through various AI providers."""

    def __init__(self):
        """Initialize the chat service."""
        self.provider_manager = AIProviderManager()
        # Import here to avoid circular dependency
        from mcp_open_client.core.manager import MCPServerManager

        self.server_manager = MCPServerManager()

    def _resolve_provider_and_model(self, request: ChatRequest) -> tuple[str, str, str]:
        """
        Resolve the provider, model name, and type based on the request.

        Returns:
            tuple: (provider_name, actual_model_name, model_type)
        """
        # Determine which provider to use
        if request.provider:
            provider_id = request.provider
            provider_config = self.provider_manager.get_provider(provider_id)
            if not provider_config:
                raise ValueError(f"Provider '{provider_id}' not found.")
        else:
            # Use default provider
            provider_config = self.provider_manager.get_default_provider()
            if not provider_config:
                raise ValueError(
                    "No default provider configured. Please set a default provider or specify one in the request."
                )
            provider_id = provider_config.id

        if not provider_config.config.enabled:
            raise ValueError(f"Provider '{provider_id}' is disabled.")

        # Determine which model to use
        model_type = request.model_type or ModelType.SMALL
        actual_model_name = request.model

        if model_type == ModelType.SMALL:
            if provider_config.config.models.small:
                actual_model_name = provider_config.config.models.small.model_name
            # If no small model configured, fall back to the provided model name
        elif model_type == ModelType.MAIN:
            if provider_config.config.models.main:
                actual_model_name = provider_config.config.models.main.model_name
            # If no main model configured, fall back to the provided model name

        return provider_id, actual_model_name, model_type.value

    def _get_openai_client(
        self,
        provider_name: str,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> OpenAI:
        """
        Get an OpenAI client configured for the specific provider.

        Args:
            provider_name: Name of the provider
            api_key: Optional API key override
            base_url: Optional base URL override

        Returns:
            OpenAI client configured for the provider
        """
        provider_config = self.provider_manager.get_provider(provider_name)
        if not provider_config:
            raise ValueError(f"Provider '{provider_name}' not found.")

        # Use overrides if provided, otherwise use provider config
        final_api_key = api_key or provider_config.config.api_key
        final_base_url = base_url or provider_config.config.base_url

        if not final_api_key:
            raise ValueError(f"No API key found for provider '{provider_name}'.")

        # Create client with appropriate configuration
        client_kwargs = {"api_key": final_api_key}
        if final_base_url:
            client_kwargs["base_url"] = final_base_url

        return OpenAI(**client_kwargs)

    def _convert_messages_for_openai(
        self, messages: List[Message]
    ) -> List[Dict[str, Any]]:
        """
        Convert our Message format to OpenAI format.

        Args:
            messages: List of messages in our format

        Returns:
            List of messages in OpenAI format
        """
        openai_messages = []
        for message in messages:
            msg_dict = {"role": message.role.value, "content": message.content}

            # Add optional fields if present
            if message.name:
                msg_dict["name"] = message.name

            if message.tool_calls:
                # Convert tool calls to OpenAI format
                tool_calls = []
                for tool_call in message.tool_calls:
                    tool_calls.append(
                        {
                            "id": tool_call.id,
                            "type": tool_call.type,
                            "function": tool_call.function,
                        }
                    )
                msg_dict["tool_calls"] = tool_calls

            if message.tool_call_id:
                msg_dict["tool_call_id"] = message.tool_call_id

            openai_messages.append(msg_dict)

        return openai_messages

    def _convert_function_call(
        self, function_call: Union[str, Dict[str, str]]
    ) -> Union[str, Dict[str, Any]]:
        """
        Convert function call format for OpenAI API.

        Args:
            function_call: Function call in our format

        Returns:
            Function call in OpenAI format
        """
        if isinstance(function_call, str):
            return function_call
        elif isinstance(function_call, dict):
            return {
                "name": function_call.get("name", ""),
                "arguments": function_call.get("arguments", ""),
            }
        return function_call

    def _get_mcp_tools(
        self, server_names: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get available tools from MCP servers and convert them to OpenAI function format.

        Args:
            server_names: Optional list of server names to get tools from. If None, gets from all running servers.

        Returns:
            List of functions in OpenAI format
        """
        try:
            # Get running servers
            servers = self.server_manager.list_servers()
            running_servers = [
                server for server in servers if server.status.value == "running"
            ]

            # Filter by server_names if provided
            if server_names:
                running_servers = [
                    server
                    for server in running_servers
                    if server.config.name in server_names
                ]

            functions = []

            for server in running_servers:
                try:
                    # Get tools from the server
                    tools_response = self.server_manager.get_server_tools(
                        server.config.name
                    )
                    if tools_response.success:
                        # Convert each tool to OpenAI function format
                        for tool in tools_response.tools:
                            function = self._convert_tool_to_function(
                                tool, server.config.name
                            )
                            functions.append(function)
                except Exception as e:
                    # Log error but continue with other servers
                    print(
                        f"Warning: Could not get tools from server '{server.config.name}': {str(e)}"
                    )
                    continue

            return functions

        except Exception as e:
            # If we can't get tools from MCP servers, return empty list
            print(f"Warning: Could not retrieve MCP tools: {str(e)}")
            return []

    def _inject_required_context_arguments(
        self, input_schema: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Inject two additional required arguments to a tool's input schema.

        These arguments force the LLM to explain:
        1. Why it's using the tool
        2. What to do in case of error

        Args:
            input_schema: Original tool input schema

        Returns:
            Modified schema with additional required arguments
        """
        # Create a copy to avoid modifying the original
        modified_schema = (
            input_schema.copy()
            if input_schema
            else {"type": "object", "properties": {}}
        )

        # Ensure properties exists
        if "properties" not in modified_schema:
            modified_schema["properties"] = {}

        # Add the two required context arguments
        modified_schema["properties"]["tool_usage_reason"] = {
            "type": "string",
            "description": "¿Para qué estás usando esta herramienta? Explica brevemente el propósito y contexto de uso.",
        }

        modified_schema["properties"]["error_handling_plan"] = {
            "type": "string",
            "description": "¿Qué debes hacer en caso de error? Describe tu plan de contingencia si la herramienta falla.",
        }

        # Update required fields
        if "required" not in modified_schema:
            modified_schema["required"] = []

        # Add to required if not already present
        if "tool_usage_reason" not in modified_schema["required"]:
            modified_schema["required"].append("tool_usage_reason")
        if "error_handling_plan" not in modified_schema["required"]:
            modified_schema["required"].append("error_handling_plan")

        return modified_schema

    def _convert_tool_to_function(
        self, tool: ToolInfo, server_name: str
    ) -> Dict[str, Any]:
        """
        Convert a ToolInfo object to OpenAI function format.

        Args:
            tool: Tool information from MCP server
            server_name: Name of the server the tool belongs to

        Returns:
            Function definition in OpenAI format
        """
        # Create a unique function name that includes the server name
        function_name = f"{server_name}_{tool.name}"

        # Use tool description or create a default one
        description = (
            tool.description or f"Tool '{tool.name}' from server '{server_name}'"
        )

        # Use the tool's input schema or create a default one
        base_schema = tool.input_schema or {
            "type": "object",
            "properties": {},
            "description": f"Parameters for {tool.name}",
        }

        # Inject required context arguments
        parameters = self._inject_required_context_arguments(base_schema)

        return {
            "name": function_name,
            "description": description,
            "parameters": parameters,
        }

    def chat_completion(self, request: ChatRequest) -> ChatResponse:
        """
        Handle a chat completion request.

        Args:
            request: Chat completion request

        Returns:
            Chat completion response
        """
        # Resolve provider and model
        provider_name, actual_model_name, model_type = self._resolve_provider_and_model(
            request
        )

        # Get OpenAI client for the provider
        client = self._get_openai_client(
            provider_name, request.api_key, request.base_url
        )

        # Convert messages to OpenAI format
        openai_messages = self._convert_messages_for_openai(request.messages)

        # Prepare request parameters
        chat_params = {
            "model": actual_model_name,
            "messages": openai_messages,
        }

        # Add optional parameters if provided
        if request.max_tokens is not None:
            chat_params["max_tokens"] = request.max_tokens
        if request.temperature is not None:
            chat_params["temperature"] = request.temperature
        if request.top_p is not None:
            chat_params["top_p"] = request.top_p
        if request.n is not None:
            chat_params["n"] = request.n
        if request.stream is not None:
            chat_params["stream"] = request.stream
        if request.logprobs is not None:
            chat_params["logprobs"] = request.logprobs
        if request.top_logprobs is not None:
            chat_params["top_logprobs"] = request.top_logprobs
        if request.echo is not None:
            chat_params["echo"] = request.echo
        if request.stop is not None:
            chat_params["stop"] = request.stop
        if request.presence_penalty is not None:
            chat_params["presence_penalty"] = request.presence_penalty
        if request.frequency_penalty is not None:
            chat_params["frequency_penalty"] = request.frequency_penalty
        if request.best_of is not None:
            chat_params["best_of"] = request.best_of
        if request.logit_bias is not None:
            chat_params["logit_bias"] = request.logit_bias
        if request.user is not None:
            chat_params["user"] = request.user
        if request.functions:
            # Convert functions to OpenAI format
            functions = []
            for func in request.functions:
                functions.append(
                    {
                        "name": func.name,
                        "description": func.description,
                        "parameters": func.parameters,
                    }
                )
            chat_params["functions"] = functions
        else:
            # Automatically get tools from MCP servers if no functions provided
            mcp_functions = self._get_mcp_tools()
            if mcp_functions:
                chat_params["functions"] = mcp_functions
                # Set function_call to "auto" to let the model decide when to use tools
                chat_params["function_call"] = "auto"

        if request.function_call:
            chat_params["function_call"] = self._convert_function_call(
                request.function_call
            )

        # Make the API call
        try:
            response = client.chat.completions.create(**chat_params)

            # Convert response to our format
            return self._convert_response(
                response, actual_model_name, provider_name, model_type
            )

        except Exception as e:
            raise Exception(f"Chat completion failed: {str(e)}")

    def _convert_response(
        self, openai_response: Any, model_name: str, provider_name: str, model_type: str
    ) -> ChatResponse:
        """
        Convert OpenAI response to our response format.

        Args:
            openai_response: Response from OpenAI client
            model_name: Name of the model used
            provider_name: Name of the provider used
            model_type: Type of model (small/main)

        Returns:
            Response in our format
        """
        # Create unique ID for the response
        response_id = f"chatcmpl-{uuid.uuid4().hex[:29]}"

        # Convert choices
        choices = []
        for choice in openai_response.choices:
            # Convert message back to our format
            message = Message(
                role=choice.message.role,
                content=choice.message.content,
                name=choice.message.name if hasattr(choice.message, "name") else None,
            )

            # Add tool calls if present
            if hasattr(choice.message, "tool_calls") and choice.message.tool_calls:
                tool_calls = []
                for tool_call in choice.message.tool_calls:
                    tool_calls.append(
                        ToolCall(
                            id=tool_call.id,
                            type=tool_call.type,
                            function=tool_call.function,
                        )
                    )
                message.tool_calls = tool_calls

            choice_dict = {
                "message": message,
                "finish_reason": choice.finish_reason,
                "index": choice.index,
            }

            # Add logprobs if present
            if hasattr(choice, "logprobs") and choice.logprobs:
                choice_dict["logprobs"] = choice.logprobs

            choices.append(Choice(**choice_dict))

        # Create usage object if present
        usage = None
        if openai_response.usage:
            usage = Usage(
                prompt_tokens=openai_response.usage.prompt_tokens,
                completion_tokens=openai_response.usage.completion_tokens,
                total_tokens=openai_response.usage.total_tokens,
            )

        return ChatResponse(
            id=response_id,
            object="chat.completion",
            created=int(time.time()),
            model=model_name,
            choices=choices,
            usage=usage,
            system_fingerprint=getattr(openai_response, "system_fingerprint", None),
        )

    def stream_chat_completion(self, request: ChatRequest):
        """
        Handle a streaming chat completion request.

        Args:
            request: Chat completion request

        Yields:
            Streaming response chunks
        """
        # Resolve provider and model
        provider_name, actual_model_name, model_type = self._resolve_provider_and_model(
            request
        )

        # Get OpenAI client for the provider
        client = self._get_openai_client(
            provider_name, request.api_key, request.base_url
        )

        # Convert messages to OpenAI format
        openai_messages = self._convert_messages_for_openai(request.messages)

        # Prepare request parameters (stream must be True for streaming)
        chat_params = {
            "model": actual_model_name,
            "messages": openai_messages,
            "stream": True,
        }

        # Add other parameters similar to non-streaming
        if request.max_tokens is not None:
            chat_params["max_tokens"] = request.max_tokens
        if request.temperature is not None:
            chat_params["temperature"] = request.temperature
        if request.top_p is not None:
            chat_params["top_p"] = request.top_p
        if request.stop is not None:
            chat_params["stop"] = request.stop
        if request.functions:
            functions = []
            for func in request.functions:
                functions.append(
                    {
                        "name": func.name,
                        "description": func.description,
                        "parameters": func.parameters,
                    }
                )
            chat_params["functions"] = functions
        if request.function_call:
            chat_params["function_call"] = self._convert_function_call(
                request.function_call
            )

        try:
            stream = client.chat.completions.create(**chat_params)
            for chunk in stream:
                yield chunk
        except Exception as e:
            raise Exception(f"Streaming chat completion failed: {str(e)}")
