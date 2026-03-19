"""
Session-based authentication for dashboard.
Uses secure cookies with HttpOnly, SameSite, and Secure flags.
"""

import os
import uuid
from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from database import User, get_db

_sessions: dict = {}

SESSION_COOKIE_NAME = "seo_session"
SESSION_EXPIRY_HOURS = int(os.getenv("SESSION_EXPIRY_HOURS", "24"))
IS_PRODUCTION = os.getenv("ENVIRONMENT", "development").lower() == "production"


def create_session(user_id: str, tenant_id: Optional[str], role: str) -> str:
    """Create a new session and return session ID."""
    session_id = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(hours=SESSION_EXPIRY_HOURS)

    _sessions[session_id] = {
        "user_id": user_id,
        "tenant_id": tenant_id,
        "role": role,
        "created_at": datetime.utcnow().isoformat(),
        "expires_at": expires_at.isoformat(),
    }

    return session_id


def get_session(session_id: str) -> Optional[dict]:
    """Get session data by ID. Returns None if expired or not found."""
    session = _sessions.get(session_id)
    if not session:
        return None

    expires_at = datetime.fromisoformat(session["expires_at"])
    if datetime.utcnow() > expires_at:
        delete_session(session_id)
        return None

    return session


def delete_session(session_id: str) -> None:
    """Delete a session (logout)."""
    _sessions.pop(session_id, None)


def update_session_tenant(session_id: str, tenant_id: str) -> bool:
    """Update the tenant_id in an existing session. Returns True if successful."""
    session = _sessions.get(session_id)
    if not session:
        return False

    session["tenant_id"] = tenant_id
    return True


def set_session_cookie(response: Response, session_id: str) -> None:
    """Set session cookie with secure flags."""
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=session_id,
        httponly=True,
        samesite="lax",
        secure=IS_PRODUCTION,
        max_age=SESSION_EXPIRY_HOURS * 3600,
        path="/dashboard",
    )


def clear_session_cookie(response: Response) -> None:
    """Clear the session cookie."""
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/dashboard",
        httponly=True,
        samesite="lax",
        secure=IS_PRODUCTION,
    )


def get_current_dashboard_user(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[dict]:
    """Get current user from session cookie. Returns None if not authenticated."""
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id:
        return None

    session = get_session(session_id)
    if not session:
        return None

    user = db.query(User).filter(User.id == session["user_id"]).first()
    if not user:
        delete_session(session_id)
        return None

    return {
        "id": user.id,
        "email": user.email,
        "role": session["role"],
        "tenant_id": session["tenant_id"],
    }


def require_dashboard_auth(
    request: Request,
    db: Session = Depends(get_db)
) -> dict:
    """Dependency that requires dashboard authentication. Raises 401 if not authenticated."""
    user = get_current_dashboard_user(request, db)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
            headers={"Location": "/dashboard/login"},
        )
    return user


def cleanup_expired_sessions() -> int:
    """Remove expired sessions. Returns count of removed sessions."""
    now = datetime.utcnow()
    expired = [
        sid for sid, session in _sessions.items()
        if datetime.fromisoformat(session["expires_at"]) < now
    ]
    for sid in expired:
        del _sessions[sid]
    return len(expired)
