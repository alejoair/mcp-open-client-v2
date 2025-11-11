"""
Chat preparation operations for conversations.
"""

from typing import Optional

from .storage import ConversationStorage


class ChatOperations:
    """Handles chat message preparation for LLM calls."""

    def __init__(self, storage: ConversationStorage):
        """Initialize chat operations."""
        self.storage = storage

    def prepare_messages(
        self, conversation_id: str, new_user_message: str
    ) -> Optional[tuple[str, list[dict[str, str]], list]]:
        """
        Prepare messages for LLM based on conversation data.

        Returns:
            tuple: (system_prompt, messages_for_llm, enabled_tools) or None if not found
        """
        conversation = self.storage.load(conversation_id)
        if not conversation:
            return None

        # Start with system prompt
        system_prompt = conversation.system_prompt

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
            messages_for_llm.append({"role": msg.role, "content": msg.content})

        # Add new user message
        messages_for_llm.append({"role": "user", "content": new_user_message})

        return system_prompt, messages_for_llm, conversation.enabled_tools
