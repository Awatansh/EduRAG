"""
Document processing task — runs as background task or Celery task.
Orchestrates: file detection → extraction → chunking → embedding → vector store.
"""

import asyncio
import traceback
from uuid import UUID

from sqlalchemy import select

from app.database import async_session
from app.models.document import Document
from app.models.chunk import Chunk
from app.services.processing.pdf_processor import extract_text_from_pdf
from app.services.processing.image_processor import extract_text_from_image
from app.services.processing.video_processor import extract_text_from_video, extract_text_from_audio
from app.services.processing.chunker import chunk_text
from app.services.embedding_service import generate_embeddings
from app.services.vector_store import upsert_vectors


async def _process_document(document_id: str):
    """
    Full document processing pipeline:
    1. Load document from DB
    2. Extract text based on file type
    3. Chunk the text
    4. Generate embeddings
    5. Store in Qdrant
    6. Save chunks to PostgreSQL
    """
    async with async_session() as db:
        try:
            # 1. Load document
            result = await db.execute(
                select(Document).where(Document.id == UUID(document_id))
            )
            document = result.scalar_one_or_none()
            if not document:
                return

            # Update status
            document.status = "processing"
            await db.commit()

            # 2. Extract text
            file_path = document.storage_path
            file_type = document.file_type

            if file_type == "pdf":
                text, page_count = await asyncio.to_thread(extract_text_from_pdf, file_path)
                document.page_count = page_count
            elif file_type == "image":
                text = await asyncio.to_thread(extract_text_from_image, file_path)
            elif file_type == "video":
                text = await asyncio.to_thread(extract_text_from_video, file_path)
            elif file_type == "audio":
                text = await asyncio.to_thread(extract_text_from_audio, file_path)
            else:
                raise ValueError(f"Unsupported file type: {file_type}")

            if not text.strip():
                document.status = "completed"
                document.error_message = "No text content extracted"
                await db.commit()
                return

            # 3. Chunk the text
            chunks_data = await asyncio.to_thread(chunk_text, text)

            if not chunks_data:
                document.status = "completed"
                await db.commit()
                return

            # 4. Generate embeddings
            chunk_texts = [c["content"] for c in chunks_data]
            embeddings = await generate_embeddings(chunk_texts)

            import uuid

            # Pre-generate chunk IDs
            chunk_ids = [uuid.uuid4() for _ in chunks_data]

            # 5. Store in Qdrant
            payloads = [
                {
                    "user_id": str(document.user_id),
                    "document_id": str(document.id),
                    "chunk_id": str(cid),
                    "chunk_index": c["chunk_index"],
                }
                for c, cid in zip(chunks_data, chunk_ids)
            ]
            vector_ids = await asyncio.to_thread(upsert_vectors, embeddings, payloads)

            # 6. Save chunks to PostgreSQL
            for chunk_data, vector_id, cid in zip(chunks_data, vector_ids, chunk_ids):
                chunk = Chunk(
                    id=cid,
                    document_id=document.id,
                    user_id=document.user_id,
                    chunk_index=chunk_data["chunk_index"],
                    content=chunk_data["content"],
                    token_count=chunk_data["token_count"],
                    vector_id=vector_id,
                )
                db.add(chunk)

            # Update document status
            document.status = "completed"
            await db.commit()

            # Update Qdrant payloads with chunk IDs (refresh from DB)
            await db.refresh(document)

        except Exception as e:
            # Mark as failed
            try:
                document.status = "failed"
                document.error_message = str(e)[:500]
                await db.commit()
            except Exception:
                pass
            traceback.print_exc()


