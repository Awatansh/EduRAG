"""
Edu Rag — FastAPI Application Entry Point
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.services.vector_store import ensure_collection


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup: ensure Qdrant collection exists
    try:
        ensure_collection()
        print("✅ Qdrant collection ready")
    except Exception as e:
        print(f"⚠️  Qdrant not available (will retry on first use): {e}")

    yield

    # Shutdown: cleanup if needed
    print("👋 Shutting down Edu Rag")


app = FastAPI(
    title="Edu Rag API",
    description="Edu Rag — Upload documents, ask questions, generate quizzes",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Register routers ────────────────────────────────────────
from app.routers import auth, documents, query, quiz  # noqa: E402

app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(query.router)
app.include_router(quiz.router)


# ── Global exception handler ────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": f"Internal server error: {str(exc)}"},
    )


# ── Health check ─────────────────────────────────────────────
@app.get("/api/health", tags=["health"])
async def health_check():
    return {"status": "ok", "service": "edu-rag"}
