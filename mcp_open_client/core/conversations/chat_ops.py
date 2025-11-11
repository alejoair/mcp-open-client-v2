"""
Chat preparation operations for conversations.
"""

from typing import Optional

from .storage import ConversationStorage
from .token_counter import TokenCounter


class ChatOperations:
    """Handles chat message preparation for LLM calls."""

    def __init__(self, storage: ConversationStorage):
        """Initialize chat operations."""
        self.storage = storage
        self.token_counter = TokenCounter()

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
            message_dict = {"role": msg.role, "content": msg.content}

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
