"""
Embedding service — generates text embeddings via configured provider.
Supports: Google Gemini (free), HuggingFace local, OpenAI.
"""

from app.config import settings


async def generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Generate embeddings for a list of texts using the configured provider."""
    provider = settings.EMBEDDING_PROVIDER.lower()

    if provider == "gemini":
        return await _embed_gemini(texts)
    elif provider == "huggingface_local":
        return _embed_huggingface_local(texts)
    elif provider == "openai":
        return await _embed_openai(texts)
    else:
        raise ValueError(f"Unknown embedding provider: {provider}")


async def generate_embedding(text: str) -> list[float]:
    """Generate embedding for a single text."""
    results = await generate_embeddings([text])
    return results[0]


# ── Provider implementations ────────────────────────────────


async def _embed_gemini(texts: list[str]) -> list[list[float]]:
    """Google Gemini text-embedding-004 (free tier)."""
    import google.generativeai as genai

    genai.configure(api_key=settings.GEMINI_API_KEY)

    embeddings = []
    # Gemini batch limit is 100 texts
    for i in range(0, len(texts), 100):
        batch = texts[i : i + 100]
        result = genai.embed_content(
            model=f"models/{settings.EMBEDDING_MODEL}",
            content=batch,
            task_type="RETRIEVAL_DOCUMENT",
        )
        if isinstance(result["embedding"][0], list):
            embeddings.extend(result["embedding"])
        else:
            embeddings.append(result["embedding"])
    return embeddings


def _embed_huggingface_local(texts: list[str]) -> list[list[float]]:
    """Local embeddings using sentence-transformers (no API needed)."""
    from sentence_transformers import SentenceTransformer

    model = SentenceTransformer(settings.EMBEDDING_MODEL)
    embeddings = model.encode(texts, normalize_embeddings=True)
    return embeddings.tolist()


async def _embed_openai(texts: list[str]) -> list[list[float]]:
    """OpenAI embeddings (paid)."""
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    response = await client.embeddings.create(
        model=settings.EMBEDDING_MODEL,
        input=texts,
    )
    return [item.embedding for item in response.data]
