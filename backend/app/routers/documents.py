"""Documents router — upload, list, detail, delete, status."""

import uuid
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, BackgroundTasks
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.document import Document
from app.schemas.document import DocumentResponse, DocumentListResponse, DocumentStatusResponse
from app.services.auth_service import get_current_user
from app.services.storage_service import save_uploaded_file, delete_document_storage
from app.services.vector_store import delete_document_vectors
from app.tasks.document_tasks import _process_document

router = APIRouter(prefix="/api/documents", tags=["documents"])

# Supported file types
SUPPORTED_TYPES = {
    "application/pdf": "pdf",
    "image/png": "image",
    "image/jpeg": "image",
    "image/jpg": "image",
    "image/tiff": "image",
    "video/mp4": "video",
    "video/mpeg": "video",
    "audio/mpeg": "audio",
    "audio/wav": "audio",
    "audio/mp3": "audio",
}


@router.post("/upload", response_model=DocumentResponse, status_code=201)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a document for processing."""
    content_type = file.content_type or ""
    file_type = SUPPORTED_TYPES.get(content_type)
    if not file_type:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {content_type}. Supported: {list(SUPPORTED_TYPES.keys())}",
        )

    # Read file content
    file_content = await file.read()
    doc_id = uuid.uuid4()

    # Save to local storage
    storage_path = await save_uploaded_file(
        user_id=current_user.id,
        document_id=doc_id,
        filename=file.filename,
        file_content=file_content,
    )

    # Create DB record
    document = Document(
        id=doc_id,
        user_id=current_user.id,
        filename=file.filename,
        file_type=file_type,
        file_size_bytes=len(file_content),
        storage_path=storage_path,
        status="pending",
    )
    db.add(document)
    await db.flush()
    await db.refresh(document)

    # Queue processing after response is sent.
    background_tasks.add_task(_process_document, str(doc_id))

    return document


@router.get("", response_model=DocumentListResponse)
async def list_documents(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all documents for the current user."""
    result = await db.execute(
        select(Document)
        .where(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
    )
    documents = result.scalars().all()

    count_result = await db.execute(
        select(func.count(Document.id)).where(Document.user_id == current_user.id)
    )
    total = count_result.scalar()

    return DocumentListResponse(documents=documents, total=total)


@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get document details."""
    result = await db.execute(
        select(Document).where(
            Document.id == document_id, Document.user_id == current_user.id
        )
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return document


@router.get("/{document_id}/status", response_model=DocumentStatusResponse)
async def get_document_status(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get document processing status."""
    result = await db.execute(
        select(Document).where(
            Document.id == document_id, Document.user_id == current_user.id
        )
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentStatusResponse(
        id=document.id, status=document.status, error_message=document.error_message
    )


@router.delete("/{document_id}", status_code=204)
async def delete_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a document, its chunks, and vector embeddings."""
    result = await db.execute(
        select(Document).where(
            Document.id == document_id, Document.user_id == current_user.id
        )
    )
    document = result.scalar_one_or_none()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.status == "processing":
        raise HTTPException(
            status_code=409,
            detail="Document is currently being processed. Please wait until processing completes before deleting.",
        )

    # Delete vectors from Qdrant
    try:
        delete_document_vectors(str(document_id))
    except Exception:
        pass  # Don't fail delete if Qdrant is down

    # Delete local files
    delete_document_storage(current_user.id, document_id)

    # Delete DB record (cascades to chunks)
    await db.delete(document)
    await db.commit()
