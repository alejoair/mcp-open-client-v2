"""
Token counting and rolling window utilities for chat endpoint.
"""

from datetime import datetime
from typing import Tuple

from mcp_open_client.core.conversations.storage import ConversationStorage
from mcp_open_client.core.conversations.token_counter import TokenCounter

from ..sse import get_local_sse_service


def apply_rolling_window(
    conversation_id: str, messages_for_llm: list, model_name: str
) -> Tuple[list, int, int]:
    """
    Apply rolling window and count tokens for current iteration.

    Returns:
        tuple: (messages_for_llm, token_count, messages_in_context)
    """
    storage = ConversationStorage()
    token_counter = TokenCounter()

    conversation = storage.load(conversation_id)
    if not conversation:
        return messages_for_llm, len(messages_for_llm) * 50, len(messages_for_llm)

    if conversation.max_tokens or conversation.max_messages:
        messages_for_llm, token_count = token_counter.apply_rolling_window(
            messages_for_llm,
            max_tokens=conversation.max_tokens,
            max_messages=conversation.max_messages,
            model=model_name,
        )
        print(
            f"[DEBUG] Rolling window applied: {len(messages_for_llm)} messages, {token_count} tokens"
        )
    else:
        token_count = token_counter.count_message_tokens(messages_for_llm, model_name)
        print(f"[DEBUG] Token count: {token_count} tokens")

    return messages_for_llm, token_count, len(messages_for_llm)


async def emit_token_update(
    conversation_id: str, messages_for_llm: list, model_name: str, iteration: int
):
    """Emit SSE token update event."""
    try:
        token_counter = TokenCounter()
        current_tokens = token_counter.count_message_tokens(
            messages_for_llm, model_name
        )

        sse_service = get_local_sse_service()
        await sse_service.emit_token_update(
            conversation_id,
            {
                "token_count": current_tokens,
                "messages_in_context": len(messages_for_llm),
                "iteration": iteration,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            },
        )
        print(f"[DEBUG] Emitted token update: {current_tokens} tokens")
    except Exception as sse_error:
        print(f"[DEBUG] SSE emit_token_update failed (non-critical): {sse_error}")
