from typing import Literal

# tiktoken is an optional dependency that's heavy to install in minimal
# dev images. Import it if available, otherwise provide a lightweight
# fallback tokenizer based on whitespace which is good enough for
# rate-limiting and approximate counts during development.
try:
    import tiktoken

    _HAS_TIKTOKEN = True
except Exception:
    tiktoken = None  # type: ignore
    _HAS_TIKTOKEN = False

APPROX_BUFFER = 1.1
TRIM_BUFFER = 0.8


def count_tokens(text: str, encoding_name="cl100k_base") -> int:
    if not text:
        return 0

    if _HAS_TIKTOKEN and tiktoken is not None:
        # Use tiktoken when available for accurate counts
        encoding = tiktoken.get_encoding(encoding_name)
        tokens = encoding.encode(text)
        return len(tokens)

    # Fallback: use a very simple whitespace-based tokenizer for
    # approximate counts in minimal development images.
    return max(1, len(text.split()))


def approximate_tokens(
    text: str,
) -> int:
    return int(count_tokens(text) * APPROX_BUFFER)


def trim_to_tokens(
    text: str,
    max_tokens: int,
    direction: Literal["start", "end"],
    ellipsis: str = "...",
) -> str:
    chars = len(text)
    tokens = count_tokens(text)

    if tokens <= max_tokens:
        return text

    approx_chars = int(chars * (max_tokens / tokens) * TRIM_BUFFER)

    if direction == "start":
        return text[:approx_chars] + ellipsis
    return ellipsis + text[chars - approx_chars : chars]
