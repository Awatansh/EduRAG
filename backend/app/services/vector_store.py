"""
Vector store service — Qdrant operations (upsert, search, delete).
"""

import uuid
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Distance,
    VectorParams,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)

from app.config import settings

_client: QdrantClient | None = None


def get_qdrant_client() -> QdrantClient:
    """Get or create Qdrant client singleton."""
    global _client
    if _client is None:
        _client = QdrantClient(host=settings.QDRANT_HOST, port=settings.QDRANT_PORT)
    return _client


def ensure_collection():
    """Create the Qdrant collection if it doesn't exist."""
    client = get_qdrant_client()
    collections = [c.name for c in client.get_collections().collections]
    if settings.QDRANT_COLLECTION not in collections:
        client.create_collection(
            collection_name=settings.QDRANT_COLLECTION,
            vectors_config=VectorParams(
                size=settings.EMBEDDING_DIMENSION,
                distance=Distance.COSINE,
            ),
        )


def upsert_vectors(
    vectors: list[list[float]],
    payloads: list[dict],
) -> list[str]:
    """
    Upsert vectors with payloads into Qdrant.
    Returns list of generated point IDs.
    """
    client = get_qdrant_client()
    point_ids = [str(uuid.uuid4()) for _ in vectors]

    points = [
        PointStruct(id=pid, vector=vec, payload=pay)
        for pid, vec, pay in zip(point_ids, vectors, payloads)
    ]

    client.upsert(collection_name=settings.QDRANT_COLLECTION, points=points)
    return point_ids


def search_vectors(
    query_vector: list[float],
    user_id: str,
    document_ids: list[str] | None = None,
    top_k: int = 5,
) -> list[dict]:
    """
    Search for similar vectors filtered by user_id (and optionally document_ids).
    Returns list of {"id", "score", "payload"}.
    """
    client = get_qdrant_client()

    must_conditions = [
        FieldCondition(key="user_id", match=MatchValue(value=user_id)),
    ]

    if document_ids:
        # OR across document IDs
        should_conditions = [
            FieldCondition(key="document_id", match=MatchValue(value=did))
            for did in document_ids
        ]
        # Wrap in a nested filter with should
        must_conditions.append(
            Filter(should=should_conditions)
        )

    results = client.search(
        collection_name=settings.QDRANT_COLLECTION,
        query_vector=query_vector,
        query_filter=Filter(must=must_conditions),
        limit=top_k,
    )

    return [
        {
            "id": str(hit.id),
            "score": hit.score,
            "payload": hit.payload,
        }
        for hit in results
    ]


def delete_document_vectors(document_id: str):
    """Delete all vectors associated with a document."""
    client = get_qdrant_client()
    client.delete(
        collection_name=settings.QDRANT_COLLECTION,
        points_selector=Filter(
            must=[
                FieldCondition(
                    key="document_id", match=MatchValue(value=document_id)
                )
            ]
        ),
    )
