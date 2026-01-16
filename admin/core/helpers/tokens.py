"""Module tokens."""

from typing import Literal

import tiktoken

APPROX_BUFFER = 1.1
TRIM_BUFFER = 0.8


def count_tokens(text: str, encoding_name="cl100k_base") -> int:
    """Execute count tokens.

    Args:
        text: The text.
        encoding_name: The encoding_name.
    """

    if not text:
        return 0

    encoding = tiktoken.get_encoding(encoding_name)
    tokens = encoding.encode(text)
    return len(tokens)


def approximate_tokens(
    text: str,
) -> int:
    """Execute approximate tokens.

    Args:
        text: The text.
    """

    return int(count_tokens(text) * APPROX_BUFFER)


def trim_to_tokens(
    text: str,
    max_tokens: int,
    direction: Literal["start", "end"],
    ellipsis: str = "...",
) -> str:
    """Execute trim to tokens.

    Args:
        text: The text.
        max_tokens: The max_tokens.
        direction: The direction.
        ellipsis: The ellipsis.
    """

    chars = len(text)
    tokens = count_tokens(text)

    if tokens <= max_tokens:
        return text

    approx_chars = int(chars * (max_tokens / tokens) * TRIM_BUFFER)

    if direction == "start":
        return text[:approx_chars] + ellipsis
    return ellipsis + text[chars - approx_chars : chars]
