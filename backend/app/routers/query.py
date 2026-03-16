"""Query router — RAG-based Q&A and chat history."""

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.quiz import ChatMessage
from app.schemas.quiz import QueryRequest, QueryResponse, ChatMessageResponse
from app.services.auth_service import get_current_user
from app.services.rag_service import rag_query

router = APIRouter(prefix="/api/query", tags=["query"])


@router.post("/ask", response_model=QueryResponse)
async def ask_question(
    request: QueryRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Ask a question — performs RAG search and returns AI answer with sources."""
    result = await rag_query(
        question=request.question,
        user_id=current_user.id,
        db=db,
        document_ids=request.document_ids,
        top_k=request.top_k,
        identity_profile=current_user.identity_profile,
    )

    # Save to chat history
    user_msg = ChatMessage(
        user_id=current_user.id,
        role="user",
        content=request.question,
    )
    assistant_msg = ChatMessage(
        user_id=current_user.id,
        role="assistant",
        content=result["answer"],
        source_chunks=result["sources"],
    )
    db.add(user_msg)
    db.add(assistant_msg)

    return QueryResponse(
        answer=result["answer"],
        sources=result["sources"],
    )


@router.get("/history", response_model=list[ChatMessageResponse])
async def get_chat_history(
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get chat history for the current user."""
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.user_id == current_user.id)
        .order_by(ChatMessage.created_at.desc())
        .limit(limit)
    )
    messages = result.scalars().all()
    return list(reversed(messages))  # return in chronological order
