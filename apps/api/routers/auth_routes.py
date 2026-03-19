"""Authentication routes."""

import re

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from apps.api.openapi import ERROR_RESPONSES, TOKEN_RESPONSE_EXAMPLE
from auth import authenticate_user, create_access_token, create_user, require_auth
from database import User, get_db

router = APIRouter(prefix="/auth", tags=["authentication"])


# Basic email pattern — catches obvious typos without requiring email-validator dep
_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")


class RegisterRequest(BaseModel):
    """Request model for user registration."""
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v):
        v = v.strip().lower()
        if not _EMAIL_RE.match(v):
            raise ValueError("Invalid email address format")
        return v

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v):
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123"
            }
        }


class LoginRequest(BaseModel):
    """Request model for user login."""
    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email_format(cls, v):
        v = v.strip().lower()
        if not _EMAIL_RE.match(v):
            raise ValueError("Invalid email address format")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "email": "user@example.com",
                "password": "securepassword123"
            }
        }


class TokenResponse(BaseModel):
    """Response model for authentication tokens."""
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str

    class Config:
        json_schema_extra = {"example": TOKEN_RESPONSE_EXAMPLE}


@router.post(
    "/register",
    response_model=TokenResponse,
    summary="Register new user",
    description="Create a new user account and receive an access token.",
    responses={
        200: {"description": "Registration successful"},
        400: ERROR_RESPONSES[400],
        422: ERROR_RESPONSES[422],
    }
)
async def register(request: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user."""
    existing = db.query(User).filter(User.email == request.email.lower()).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    user = create_user(db, request.email, request.password)
    token = create_access_token(user.id, user.role)

    return TokenResponse(access_token=token, user_id=user.id, email=user.email)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login",
    description="Authenticate with email and password to receive an access token.",
    responses={
        200: {"description": "Login successful"},
        401: ERROR_RESPONSES[401],
        422: ERROR_RESPONSES[422],
    }
)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Login and get access token."""
    user = authenticate_user(db, request.email, request.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token(user.id, user.role)
    return TokenResponse(access_token=token, user_id=user.id, email=user.email)


@router.get(
    "/me",
    summary="Get current user",
    description="Get information about the currently authenticated user.",
    responses={
        200: {
            "description": "Current user info",
            "content": {
                "application/json": {
                    "example": {"user_id": "user_xyz789", "email": "user@example.com", "role": "user"}
                }
            }
        },
        401: ERROR_RESPONSES[401],
    }
)
async def get_me(user: User = Depends(require_auth)):
    """Get current user info."""
    return {"user_id": user.id, "email": user.email, "role": user.role}
