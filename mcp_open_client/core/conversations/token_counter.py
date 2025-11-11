"""Token counting utilities for conversations."""

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
                    # Convert to string if needed
                    text = str(value) if not isinstance(value, str) else value
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

        Returns:
            tuple: (filtered_messages, total_token_count)
        """
        if not messages:
            return messages, 0

        # Apply max_messages limit first (simpler)
        if max_messages is not None and len(messages) > max_messages:
            messages = messages[-max_messages:]

        # Apply max_tokens limit (more complex)
        if max_tokens is not None:
            encoding = self._get_encoding(model)
            tokens_per_message = 3
            tokens_per_name = 1

            # Build messages from newest to oldest until we hit token limit
            filtered = []
            current_tokens = 3  # Priming tokens

            # Iterate backwards through messages
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
                    break

                filtered.insert(0, message)
                current_tokens += msg_tokens

            messages = filtered

        # Count final token total
        total_tokens = self.count_message_tokens(messages, model)

        return messages, total_tokens
