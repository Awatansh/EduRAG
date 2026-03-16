"""
Quiz service — generates quizzes from document chunks via LLM.
"""

import json
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.chunk import Chunk
from app.services.embedding_service import generate_embedding
from app.services.vector_store import search_vectors
from app.services.rag_service import _call_llm


QUIZ_PROMPT_TEMPLATE = """Based on the following content from documents, generate a quiz.

Content:
{context}

Generate exactly {num_questions} questions of type "{quiz_type}".

Return ONLY a valid JSON array with this exact schema:
[
  {{
    "question": "the question text",
    "type": "{quiz_type}",
    "options": ["A", "B", "C", "D"],  // for mcq/true_false; null for short_answer
    "correct_answer": "the correct answer",
    "explanation": "brief explanation of the correct answer"
  }}
]

Ensure questions are clear, educational, and cover key concepts from the content."""


async def generate_quiz(
    user_id: UUID,
    document_ids: list[UUID],
    quiz_type: str,
    num_questions: int,
    db: AsyncSession,
) -> list[dict]:
    """
    Generate quiz questions from specified documents.
    1. Retrieve relevant chunks
    2. Build prompt
    3. Call LLM for structured quiz output
    4. Parse and return questions
    """
    # Retrieve chunks from specified documents
    query = (
        select(Chunk)
        .where(Chunk.user_id == user_id)
        .where(Chunk.document_id.in_(document_ids))
        .order_by(Chunk.chunk_index)
        .limit(20)  # use top 20 chunks for quiz context
    )
    result = await db.execute(query)
    chunks = result.scalars().all()

    if not chunks:
        raise ValueError("No content found in the specified documents.")

    context = "\n\n---\n\n".join(c.content for c in chunks)

    # Build prompt
    user_prompt = QUIZ_PROMPT_TEMPLATE.format(
        context=context,
        num_questions=num_questions,
        quiz_type=quiz_type,
    )
    system_prompt = (
        "You are an educational quiz generator. Generate well-structured quizzes "
        "based on provided content. Always return valid JSON."
    )

    # Call LLM
    raw_response = await _call_llm(system_prompt, user_prompt)

    # Parse JSON from response
    questions = _parse_quiz_response(raw_response)
    return questions


def _parse_quiz_response(raw: str) -> list[dict]:
    """Parse LLM response into quiz questions JSON."""
    # Try to extract JSON from the response
    raw = raw.strip()

    # Handle case where LLM wraps in markdown code block
    if raw.startswith("```"):
        lines = raw.split("\n")
        json_lines = []
        in_block = False
        for line in lines:
            if line.startswith("```") and not in_block:
                in_block = True
                continue
            elif line.startswith("```") and in_block:
                break
            elif in_block:
                json_lines.append(line)
        raw = "\n".join(json_lines)

    try:
        questions = json.loads(raw)
        if isinstance(questions, list):
            return questions
        raise ValueError("Expected a JSON array")
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse quiz response as JSON: {e}")


def score_quiz(questions: list[dict], answers: dict) -> float:
    """
    Score submitted quiz answers.
    answers: {question_index: user_answer}
    Returns score as percentage (0.0 - 100.0).
    """
    if not questions:
        return 0.0

    correct = 0
    total = len(questions)

    for i, q in enumerate(questions):
        user_answer = answers.get(str(i), "")
        if user_answer.strip().lower() == q.get("correct_answer", "").strip().lower():
            correct += 1

    return round((correct / total) * 100, 2)
