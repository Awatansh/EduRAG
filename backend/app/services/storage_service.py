"""Storage service — local file storage management."""

import shutil
from pathlib import Path
from uuid import UUID

from app.config import settings


def get_user_storage_dir(user_id: UUID) -> Path:
    """Return the storage directory for a user, creating it if needed."""
    base = Path(settings.LOCAL_STORAGE_PATH)
    user_dir = base / str(user_id)
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


def get_document_storage_dir(user_id: UUID, document_id: UUID) -> Path:
    """Return the storage directory for a specific document."""
    doc_dir = get_user_storage_dir(user_id) / str(document_id)
    doc_dir.mkdir(parents=True, exist_ok=True)
    return doc_dir


async def save_uploaded_file(
    user_id: UUID,
    document_id: UUID,
    filename: str,
    file_content: bytes,
) -> str:
    """Save uploaded file to local storage, return the file path."""
    doc_dir = get_document_storage_dir(user_id, document_id)
    file_path = doc_dir / filename
    file_path.write_bytes(file_content)
    return str(file_path)


def delete_document_storage(user_id: UUID, document_id: UUID) -> None:
    """Delete all stored files for a document."""
    doc_dir = get_document_storage_dir(user_id, document_id)
    if doc_dir.exists():
        shutil.rmtree(doc_dir)
