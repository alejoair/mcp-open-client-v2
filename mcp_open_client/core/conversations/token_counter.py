"""Token counting utilities for conversations."""

import json
from typing import Any, Dict, List, Optional

import tiktoken


class TokenCounter:
    """Handles token counting for messages."""

    def __init__(self):
        self.encodings = {}

    def _get_encoding(self, model: str) -> tiktoken.Encoding:
        """Get or create encoding for model."""
        if model not in self.encodings:
            try:
                self.encodings[model] = tiktoken.encoding_for_model(model)
            except KeyError:
                # Fallback to o200k_base for unknown models
                self.encodings[model] = tiktoken.get_encoding("o200k_base")
        return self.encodings[model]

    def count_message_tokens(
        self, messages: List[Dict[str, Any]], model: str = "gpt-4o"
    ) -> int:
        """Count tokens in a list of messages."""
        encoding = self._get_encoding(model)

        # GPT-4o and similar models use 3 tokens per message
        tokens_per_message = 3
        tokens_per_name = 1

        num_tokens = 0
        for message in messages:
            num_tokens += tokens_per_message
            for key, value in message.items():
                if value is not None:
                    # Handle complex structures (tool_calls, etc.)
                    if isinstance(value, (list, dict)):
                        text = json.dumps(value)
                    elif isinstance(value, str):
                        text = value
                    else:
                        text = str(value)
                    num_tokens += len(encoding.encode(text))
                    if key == "name":
                        num_tokens += tokens_per_name

        # Priming tokens for assistant response
        num_tokens += 3
        return num_tokens

    def apply_rolling_window(
        self,
        messages: List[Dict[str, Any]],
        max_tokens: Optional[int] = None,
        max_messages: Optional[int] = None,
        model: str = "gpt-4o",
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        Apply rolling window to messages based on token count or message count.
        Ensures tool call/response pairs are kept together.

        Returns:
            tuple: (filtered_messages, total_token_count)
        """
        if not messages:
            return messages, 0

        # First, verify tool integrity and clean orphaned tool responses
        messages = self._verify_tool_integrity(messages)

        # Apply max_messages limit first (simpler)
        if max_messages is not None and len(messages) > max_messages:
            messages = self._safe_apply_max_messages(messages, max_messages)

        # Apply max_tokens limit (more complex)
        if max_tokens is not None:
            messages = self._safe_apply_max_tokens(messages, max_tokens, model)

        # Final verification to ensure tool integrity
        # This is a safety check in case any edge cases were missed
        messages = self._verify_tool_integrity(messages)

        # Count final token total
        total_tokens = self.count_message_tokens(messages, model)

        return messages, total_tokens

    def _verify_tool_integrity(
        self, messages: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Remove orphaned tool responses that don't have corresponding tool calls.
        A tool response is orphaned if there's no assistant message with a matching tool_call_id.
        """
        # First pass: collect all valid tool_call_ids from assistant messages
        valid_tool_call_ids = set()
        for message in messages:
            if message.get("role") == "assistant" and message.get("tool_calls"):
                for tool_call in message.get("tool_calls", []):
                    if isinstance(tool_call, dict) and "id" in tool_call:
                        valid_tool_call_ids.add(tool_call["id"])

        # Second pass: filter messages, keeping only tool responses with valid tool_call_ids
        verified = []
        for message in messages:
            if message.get("role") == "tool":
                tool_call_id = message.get("tool_call_id")
                if tool_call_id and tool_call_id in valid_tool_call_ids:
                    # Valid tool response, keep it
                    verified.append(message)
                else:
                    # Orphaned tool response, skip it
                    print(
                        f"[DEBUG] Removed orphaned tool response: {message.get('name', 'unknown')} (tool_call_id: {tool_call_id})"
                    )
            else:
                # Not a tool response, keep it
                verified.append(message)

        return verified

    def _safe_apply_max_messages(
        self, messages: List[Dict[str, Any]], max_messages: int
    ) -> List[Dict[str, Any]]:
        """
        Apply max_messages limit while maintaining tool call/response pairs.
        """
        if len(messages) <= max_messages:
            return messages

        # Get the last max_messages messages first
        trimmed = messages[-max_messages:]

        # Now ensure tool pairs are intact in the trimmed list
        return self._verify_tool_integrity(trimmed)

    def _safe_apply_max_tokens(
        self, messages: List[Dict[str, Any]], max_tokens: int, model: str
    ) -> List[Dict[str, Any]]:
        """
        Apply max_tokens limit while maintaining tool call/response pairs.
        """
        encoding = self._get_encoding(model)
        tokens_per_message = 3
        tokens_per_name = 1

        # Build messages from newest to oldest until we hit token limit
        filtered = []
        current_tokens = 3  # Priming tokens

        # Process from newest to oldest
        for message in reversed(messages):
            # Count tokens for this message
            msg_tokens = tokens_per_message
            for key, value in message.items():
                if value is not None:
                    text = str(value) if not isinstance(value, str) else value
                    msg_tokens += len(encoding.encode(text))
                    if key == "name":
                        msg_tokens += tokens_per_name

            # Check if adding this message would exceed limit
            if current_tokens + msg_tokens > max_tokens:
                # This message would exceed the limit, stop here
                break

            # Add message to filtered list
            filtered.insert(0, message)
            current_tokens += msg_tokens

        # Verify tool integrity before returning
        # This ensures no orphaned tool_calls or tool responses remain
        return self._verify_tool_integrity(filtered)
