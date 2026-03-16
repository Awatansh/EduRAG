"""Pydantic schemas for User endpoints."""

import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr


# ── Request schemas ──────────────────────────────────────────

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str | None = None


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserProfileUpdate(BaseModel):
    full_name: str | None = None
    identity_profile: dict | None = None


# ── Response schemas ─────────────────────────────────────────

class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    full_name: str | None
    identity_profile: dict
    created_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
