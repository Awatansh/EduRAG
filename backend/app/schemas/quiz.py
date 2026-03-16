"""Pydantic schemas for Quiz and Query endpoints."""

import uuid
from datetime import datetime
from pydantic import BaseModel


# ── Query / RAG ──────────────────────────────────────────────

class QueryRequest(BaseModel):
    question: str
    document_ids: list[uuid.UUID] | None = None  # filter to specific docs
    top_k: int = 5


class SourceChunk(BaseModel):
    chunk_id: uuid.UUID
    document_id: uuid.UUID
    content_preview: str
    score: float


class QueryResponse(BaseModel):
    answer: str
    sources: list[SourceChunk]


class ChatMessageResponse(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    source_chunks: list
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Quiz ─────────────────────────────────────────────────────

class QuizGenerateRequest(BaseModel):
    document_ids: list[uuid.UUID]
    quiz_type: str = "mcq"  # mcq | true_false | short_answer | mixed
    num_questions: int = 5


class QuizSubmitRequest(BaseModel):
    answers: dict  # { question_index: selected_answer }


class QuizResponse(BaseModel):
    id: uuid.UUID
    title: str | None
    quiz_type: str
    num_questions: int | None
    questions: dict | list
    score: float | None
    submitted_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}
