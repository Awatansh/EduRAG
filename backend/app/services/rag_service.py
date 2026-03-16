"""
RAG service — retrieval-augmented generation pipeline.
Supports: Groq (free), Google Gemini (free), OpenAI, Ollama.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.chunk import Chunk
from app.services.embedding_service import generate_embedding
from app.services.vector_store import search_vectors


async def rag_query(
    question: str,
    user_id: UUID,
    db: AsyncSession,
    document_ids: list[UUID] | None = None,
    top_k: int = 5,
    identity_profile: dict | None = None,
) -> dict:
    """
    Full RAG pipeline:
    1. Embed the question
    2. Search Qdrant for relevant chunks
    3. Retrieve chunk content from PostgreSQL
    4. Build prompt with context + identity
    5. Call LLM
    Returns {"answer": str, "sources": list[dict]}
    """
    # 1. Embed question
    query_vector = await generate_embedding(question)

    # 2. Vector search
    doc_id_strs = [str(d) for d in document_ids] if document_ids else None
    search_results = search_vectors(
        query_vector=query_vector,
        user_id=str(user_id),
        document_ids=doc_id_strs,
        top_k=top_k,
    )

    if not search_results:
        return {
            "answer": "I couldn't find any relevant information in your documents to answer this question.",
            "sources": [],
        }

    # 3. Retrieve chunk content from DB
    chunk_ids = [UUID(r["payload"]["chunk_id"]) for r in search_results]
    result = await db.execute(select(Chunk).where(Chunk.id.in_(chunk_ids)))
    chunks = {str(c.id): c for c in result.scalars().all()}

    # 4. Build context
    context_parts = []
    sources = []
    for sr in search_results:
        chunk_id = sr["payload"]["chunk_id"]
        chunk = chunks.get(chunk_id)
        if chunk:
            context_parts.append(chunk.content)
            sources.append({
                "chunk_id": chunk_id,
                "document_id": sr["payload"]["document_id"],
                "content_preview": chunk.content[:200],
                "score": sr["score"],
            })

    context = "\n\n---\n\n".join(context_parts)

    # 5. Build prompt & call LLM
    system_prompt = _build_system_prompt(identity_profile)
    user_prompt = f"""Based on the following context from the user's documents, answer the question.

Context:
{context}

Question: {question}

Provide a clear, accurate answer based on the context. If the context doesn't contain enough information, say so."""

    answer = await _call_llm(system_prompt, user_prompt)

    return {"answer": answer, "sources": sources}


def _build_system_prompt(identity_profile: dict | None = None) -> str:
    """Build system prompt, optionally incorporating user identity profile."""
    base = (
        "You are a helpful knowledge assistant. You answer questions based on the user's "
        "uploaded documents. Be accurate, concise, and cite relevant parts of the context."
    )
    if identity_profile:
        prefs = ", ".join(f"{k}: {v}" for k, v in identity_profile.items())
        base += f"\n\nUser profile: {prefs}. Tailor your response style accordingly."
    return base


async def _call_llm(system_prompt: str, user_prompt: str) -> str:
    """Call configured LLM provider."""
    provider = settings.LLM_PROVIDER.lower()

    if provider == "groq":
        return await _call_groq(system_prompt, user_prompt)
    elif provider == "gemini":
        return await _call_gemini(system_prompt, user_prompt)
    elif provider == "openai":
        return await _call_openai(system_prompt, user_prompt)
    elif provider == "ollama":
        return await _call_ollama(system_prompt, user_prompt)
    else:
        raise ValueError(f"Unknown LLM provider: {provider}")


async def _call_groq(system_prompt: str, user_prompt: str) -> str:
    """Groq free tier — Llama 3.3 70B."""
    from groq import AsyncGroq

    client = AsyncGroq(api_key=settings.GROQ_API_KEY)
    response = await client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=2048,
    )
    return response.choices[0].message.content


async def _call_gemini(system_prompt: str, user_prompt: str) -> str:
    """Google Gemini free tier."""
    import google.generativeai as genai

    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel(
        settings.GEMINI_LLM_MODEL,
        system_instruction=system_prompt,
    )
    response = model.generate_content(user_prompt)
    return response.text


async def _call_openai(system_prompt: str, user_prompt: str) -> str:
    """OpenAI API (paid)."""
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    response = await client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.3,
        max_tokens=2048,
    )
    return response.choices[0].message.content


async def _call_ollama(system_prompt: str, user_prompt: str) -> str:
    """Local Ollama."""
    import httpx

    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{settings.OLLAMA_BASE_URL}/api/chat",
            json={
                "model": settings.OLLAMA_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                "stream": False,
            },
            timeout=120.0,
        )
        response.raise_for_status()
        return response.json()["message"]["content"]
