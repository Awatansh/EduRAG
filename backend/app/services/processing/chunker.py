"""Text chunker — splits extracted text into overlapping chunks."""

import tiktoken


def count_tokens(text: str, model: str = "cl100k_base") -> int:
    """Count tokens in text using tiktoken."""
    enc = tiktoken.get_encoding(model)
    return len(enc.encode(text))


def chunk_text(
    text: str,
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
    separators: list[str] | None = None,
) -> list[dict]:
    """
    Split text into overlapping chunks, preserving sentence boundaries.
    Returns list of {"content": str, "token_count": int, "chunk_index": int}.
    """
    if separators is None:
        separators = ["\n\n", "\n", ". ", " "]

    chunks = []
    current_text = text.strip()

    if not current_text:
        return chunks

    # Simple recursive splitting
    segments = _recursive_split(current_text, chunk_size, separators)

    # Build overlapping chunks
    for i, segment in enumerate(segments):
        chunks.append({
            "content": segment.strip(),
            "token_count": count_tokens(segment),
            "chunk_index": i,
        })

    return chunks


def _recursive_split(text: str, max_tokens: int, separators: list[str]) -> list[str]:
    """Recursively split text by separators until chunks are within max_tokens."""
    if count_tokens(text) <= max_tokens:
        return [text]

    if not separators:
        # Hard split by characters as last resort
        words = text.split()
        mid = len(words) // 2
        left = " ".join(words[:mid])
        right = " ".join(words[mid:])
        return _recursive_split(left, max_tokens, []) + _recursive_split(right, max_tokens, [])

    sep = separators[0]
    parts = text.split(sep)

    result = []
    current_chunk = ""

    for part in parts:
        candidate = current_chunk + sep + part if current_chunk else part
        if count_tokens(candidate) <= max_tokens:
            current_chunk = candidate
        else:
            if current_chunk:
                result.append(current_chunk)
            # If single part exceeds limit, split further
            if count_tokens(part) > max_tokens:
                result.extend(_recursive_split(part, max_tokens, separators[1:]))
                current_chunk = ""
            else:
                current_chunk = part

    if current_chunk:
        result.append(current_chunk)

    return result
