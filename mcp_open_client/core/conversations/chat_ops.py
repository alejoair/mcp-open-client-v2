"""
Chat preparation operations for conversations.
"""

import json
import uuid
from datetime import datetime
from typing import Optional

from .storage import ConversationStorage
from .token_counter import TokenCounter

# Force reload marker
print("[CHAT_OPS_MODULE] Module loaded/reloaded")


class ChatOperations:
    """Handles chat message preparation for LLM calls."""

    def __init__(self, storage: ConversationStorage):
        """Initialize chat operations."""
        self.storage = storage
        self.token_counter = TokenCounter()

    def _clean_tool_message_content(self, content: str) -> str:
        """
        Clean tool message content that may contain CallToolResult objects.

        Args:
            content: Raw content that may be in CallToolResult format

        Returns:
            Cleaned JSON string
        """
        if not content or not isinstance(content, str):
            return content

        # Check if it's a CallToolResult string representation
        if content.startswith("CallToolResult("):
            try:
                # Extract the text content from CallToolResult
                import re

                text_match = re.search(
                    r"text='([^']+(?:\\'[^']*)*)'|text=\"([^\"]+(?:\\\"[^\"]*)*)\"",
                    content,
                )
                if text_match:
                    extracted = text_match.group(1) or text_match.group(2)
                    # Unescape the content
                    cleaned = (
                        extracted.replace("\\n", "\n")
                        .replace('\\"', '"')
                        .replace("\\'", "'")
                    )
                    return cleaned
            except Exception as e:
                print(
                    f"[CHAT_OPS] Warning: Failed to clean CallToolResult content: {e}"
                )

        return content

    def _fix_incomplete_tool_calls(
        self, conversation_id: str, messages_for_llm: list[dict]
    ) -> list[dict]:
        """
        Validate and fix incomplete tool calls in message history.

        When the server crashes during tool execution, assistant messages with
        tool_calls may not have corresponding tool response messages. This causes
        OpenAI API errors. This method detects and fixes such cases by:
        1. Finding all tool_call_ids that need responses
        2. Adding error response messages for missing tool_call_ids
        3. Persisting the error responses to the conversation

        Args:
            conversation_id: Conversation identifier
            messages_for_llm: List of messages prepared for LLM

        Returns:
            Fixed list of messages with all tool calls having responses
        """
        # Track which tool_call_ids need responses
        pending_tool_calls = {}  # tool_call_id -> tool info
        fixed_messages = []
        messages_to_persist = []  # New tool response messages to save

        for msg in messages_for_llm:
            # If we encounter a non-tool message and there are pending tool calls,
            # insert error responses BEFORE this message
            if msg.get("role") != "tool" and pending_tool_calls:
                print(
                    f"[TOOL_CALL_FIX] Found {len(pending_tool_calls)} incomplete tool calls before {msg.get('role')} message, inserting error responses"
                )

                for tool_call_id, info in pending_tool_calls.items():
                    tool_name = info["name"]
                    error_response = json.dumps(
                        {
                            "error": "Tool execution was interrupted (server crash/restart). Please try again.",
                            "tool_call_id": tool_call_id,
                            "tool_name": tool_name,
                        }
                    )

                    # Create tool response message and insert BEFORE current message
                    tool_msg = {
                        "role": "tool",
                        "content": error_response,
                        "tool_call_id": tool_call_id,
                        "name": tool_name,
                    }
                    fixed_messages.append(tool_msg)

                    # Create message to persist
                    msg_id = f"msg-{uuid.uuid4().hex[:16]}"
                    timestamp = datetime.utcnow().isoformat() + "Z"
                    messages_to_persist.append(
                        {
                            "id": msg_id,
                            "role": "tool",
                            "content": error_response,
                            "timestamp": timestamp,
                            "tool_call_id": tool_call_id,
                            "name": tool_name,
                        }
                    )

                    print(
                        f"[TOOL_CALL_FIX] Added error response for tool_call_id={tool_call_id}, tool={tool_name}"
                    )

                # Clear pending after inserting error responses
                pending_tool_calls = {}

            # Now add the current message
            fixed_messages.append(msg)

            # If assistant message has tool_calls, track them
            if msg.get("role") == "assistant" and msg.get("tool_calls"):
                for tool_call in msg["tool_calls"]:
                    tool_call_id = tool_call.get("id")
                    if tool_call_id:
                        pending_tool_calls[tool_call_id] = {
                            "name": tool_call.get("function", {}).get(
                                "name", "unknown"
                            ),
                            "tool_call": tool_call,
                        }

            # If tool message, mark its tool_call_id as resolved
            elif msg.get("role") == "tool":
                tool_call_id = msg.get("tool_call_id")
                if tool_call_id and tool_call_id in pending_tool_calls:
                    del pending_tool_calls[tool_call_id]

        # Handle any remaining pending tool calls at the end
        # (this happens if the last message is an assistant message with tool_calls)
        if pending_tool_calls:
            print(
                f"[TOOL_CALL_FIX] Found {len(pending_tool_calls)} incomplete tool calls at end, adding error responses"
            )

            for tool_call_id, info in pending_tool_calls.items():
                tool_name = info["name"]
                error_response = json.dumps(
                    {
                        "error": "Tool execution was interrupted (server crash/restart). Please try again.",
                        "tool_call_id": tool_call_id,
                        "tool_name": tool_name,
                    }
                )

                # Create tool response message
                tool_msg = {
                    "role": "tool",
                    "content": error_response,
                    "tool_call_id": tool_call_id,
                    "name": tool_name,
                }
                fixed_messages.append(tool_msg)

                # Create message to persist
                msg_id = f"msg-{uuid.uuid4().hex[:16]}"
                timestamp = datetime.utcnow().isoformat() + "Z"
                messages_to_persist.append(
                    {
                        "id": msg_id,
                        "role": "tool",
                        "content": error_response,
                        "timestamp": timestamp,
                        "tool_call_id": tool_call_id,
                        "name": tool_name,
                    }
                )

                print(
                    f"[TOOL_CALL_FIX] Added error response for tool_call_id={tool_call_id}, tool={tool_name}"
                )

        # Persist the new tool messages to the conversation
        if messages_to_persist:
            conversation = self.storage.load(conversation_id)
            if conversation:
                from mcp_open_client.api.models.conversation import Message

                for msg_data in messages_to_persist:
                    new_message = Message(**msg_data)
                    conversation.messages.append(new_message)
                    conversation.updated_at = datetime.utcnow().isoformat() + "Z"

                self.storage.save(conversation)
                print(
                    f"[TOOL_CALL_FIX] Persisted {len(messages_to_persist)} error responses to conversation"
                )

        return fixed_messages

    def prepare_messages(
        self, conversation_id: str, new_user_message: str
    ) -> Optional[tuple[str, list[dict[str, str]], list, int, int]]:
        """
        Prepare messages for LLM based on conversation data.

        Returns:
            tuple: (system_prompt, messages_for_llm, enabled_tools, token_count, messages_in_context) or None if not found
        """
        # Use gpt-4o as standard model for token counting
        model = "gpt-4o"
        conversation = self.storage.load(conversation_id)
        if not conversation:
            return None

        # Start with system prompt
        system_prompt = conversation.system_prompt

        # Add conversation ID information
        conversation_info = "\n\n## Conversation Context\n\n"
        conversation_info += (
            f"You are currently in conversation ID: `{conversation_id}`\n"
        )
        conversation_info += "When using tools that require a `conversation_id` parameter, you MUST use this exact ID.\n"
        system_prompt += conversation_info

        # Add tools section to clarify available tools
        if conversation.enabled_tools:
            tools_section = "\n\n## Available Tools\n\n"
            tools_section += (
                "You have access to the following external tools/functions. "
                "Use them when appropriate to help the user:\n\n"
            )
            for tool in conversation.enabled_tools:
                tools_section += f"- {tool.tool_name}\n"
            system_prompt += tools_section
        else:
            # Explicitly state no tools available to prevent hallucination
            no_tools_section = "\n\n## Available Tools\n\n"
            no_tools_section += (
                "You do NOT have access to any external tools, functions, or capabilities "
                "beyond your training knowledge. Do not claim to have web search, code execution, "
                "image generation, or any other special tools. If asked about tools, clearly state "
                "that you don't have any tools available in this conversation."
            )
            system_prompt += no_tools_section

        # Add context section if there are context items
        if conversation.context:
            context_section = "\n\n## Context Information\n\n"
            for ctx_id, ctx_item in conversation.context.items():
                context_section += f"### {ctx_item.descriptive_name}\n"
                context_section += f"**Context ID:** `{ctx_id}`\n\n"
                if ctx_item.related_keywords:
                    context_section += (
                        f"Keywords: {', '.join(ctx_item.related_keywords)}\n"
                    )
                if ctx_item.related_files:
                    context_section += (
                        f"Related files: {', '.join(ctx_item.related_files)}\n"
                    )
                context_section += f"\n{ctx_item.content}\n\n"
            system_prompt += context_section

        # Build messages array with conversation history
        messages_for_llm = []

        # Add previous messages
        for msg in conversation.messages:
            # Clean tool message content if needed
            content = msg.content
            if msg.role == "tool":
                content = self._clean_tool_message_content(content)

            message_dict = {"role": msg.role, "content": content}

            # Add tool_calls for assistant messages
            if msg.role == "assistant" and msg.tool_calls:
                message_dict["tool_calls"] = msg.tool_calls

            # Add tool_call_id and name for tool messages
            if msg.role == "tool":
                if msg.tool_call_id:
                    message_dict["tool_call_id"] = msg.tool_call_id
                if msg.name:
                    message_dict["name"] = msg.name

            messages_for_llm.append(message_dict)

        # Add new user message
        messages_for_llm.append({"role": "user", "content": new_user_message})

        # Fix incomplete tool calls before sending to LLM
        # This prevents OpenAI API errors when server crashed during tool execution
        try:
            print(
                f"[CHAT_OPS] About to fix incomplete tool calls for conversation {conversation_id}"
            )
            messages_for_llm = self._fix_incomplete_tool_calls(
                conversation_id, messages_for_llm
            )
            print(f"[CHAT_OPS] Tool call fix completed successfully")
        except Exception as e:
            print(f"[CHAT_OPS] Error fixing incomplete tool calls: {e}")
            import traceback

            traceback.print_exc()

        # Apply rolling window if configured
        if conversation.max_tokens or conversation.max_messages:
            messages_for_llm, token_count = self.token_counter.apply_rolling_window(
                messages_for_llm,
                max_tokens=conversation.max_tokens,
                max_messages=conversation.max_messages,
                model=model,
            )
        else:
            # Just count tokens without applying window
            token_count = self.token_counter.count_message_tokens(
                messages_for_llm, model
            )

        messages_in_context = len(messages_for_llm)

        return (
            system_prompt,
            messages_for_llm,
            conversation.enabled_tools,
            token_count,
            messages_in_context,
        )
