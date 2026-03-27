"""
Utility functions for the LM Code CLI tool.
"""

import tiktoken
import json


def count_tokens(text):
    """
    Count the number of tokens in a text string.
    Uses GPT-4 tokenizer as a proxy.
    """
    try:
        encoding = tiktoken.encoding_for_model("gpt-4")
        return len(encoding.encode(text))
    except Exception:
        # Fallback method: roughly 4 chars per token
        return len(text) // 4
