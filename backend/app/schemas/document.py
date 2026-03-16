"""Pydantic schemas for Document endpoints."""

import uuid
from datetime import datetime
from pydantic import BaseModel


class DocumentResponse(BaseModel):
    id: uuid.UUID
    filename: str
    file_type: str
    file_size_bytes: int | None
    status: str
    error_message: str | None
    page_count: int | None
    metadata_: dict
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    documents: list[DocumentResponse]
    total: int


class DocumentStatusResponse(BaseModel):
    id: uuid.UUID
    status: str
    error_message: str | None
