"""Quiz router — generate, list, detail, submit."""

import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.user import User
from app.models.quiz import Quiz
from app.schemas.quiz import QuizGenerateRequest, QuizSubmitRequest, QuizResponse
from app.services.auth_service import get_current_user
from app.services.quiz_service import generate_quiz, score_quiz

router = APIRouter(prefix="/api/quiz", tags=["quiz"])


@router.post("/generate", response_model=QuizResponse, status_code=201)
async def generate_quiz_endpoint(
    request: QuizGenerateRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate a quiz from specified documents."""
    try:
        questions = await generate_quiz(
            user_id=current_user.id,
            document_ids=request.document_ids,
            quiz_type=request.quiz_type,
            num_questions=request.num_questions,
            db=db,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    quiz = Quiz(
        user_id=current_user.id,
        title=f"{request.quiz_type.upper()} Quiz ({request.num_questions} questions)",
        document_ids=[str(d) for d in request.document_ids],
        quiz_type=request.quiz_type,
        num_questions=request.num_questions,
        questions=questions,
    )
    db.add(quiz)
    await db.flush()
    await db.refresh(quiz)
    return quiz


@router.get("", response_model=list[QuizResponse])
async def list_quizzes(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all quizzes for the current user."""
    result = await db.execute(
        select(Quiz)
        .where(Quiz.user_id == current_user.id)
        .order_by(Quiz.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{quiz_id}", response_model=QuizResponse)
async def get_quiz(
    quiz_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get quiz details."""
    result = await db.execute(
        select(Quiz).where(Quiz.id == quiz_id, Quiz.user_id == current_user.id)
    )
    quiz = result.scalar_one_or_none()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    return quiz


@router.post("/{quiz_id}/submit", response_model=QuizResponse)
async def submit_quiz(
    quiz_id: uuid.UUID,
    request: QuizSubmitRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit quiz answers and get score."""
    result = await db.execute(
        select(Quiz).where(Quiz.id == quiz_id, Quiz.user_id == current_user.id)
    )
    quiz = result.scalar_one_or_none()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")

    if quiz.submitted_at:
        raise HTTPException(status_code=400, detail="Quiz already submitted")

    quiz.score = score_quiz(quiz.questions, request.answers)
    quiz.submitted_at = datetime.now(timezone.utc)
    await db.flush()
    await db.refresh(quiz)
    return quiz


@router.delete("/{quiz_id}", status_code=204)
async def delete_quiz(
    quiz_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a quiz."""
    result = await db.execute(
        select(Quiz).where(Quiz.id == quiz_id, Quiz.user_id == current_user.id)
    )
    quiz = result.scalar_one_or_none()
    if not quiz:
        raise HTTPException(status_code=404, detail="Quiz not found")
    await db.delete(quiz)
    await db.commit()
