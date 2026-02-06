"""
Authentication module with JWT tokens.
"""

import hashlib
import os
import uuid
from datetime import datetime, timedelta
from typing import Optional

import bcrypt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from database import User, get_db

# Configuration
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "dev-secret-key-change-in-production")
ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_HOURS = int(os.getenv("JWT_EXPIRE_HOURS", "24"))

# Fail fast if default secret is used in production
if SECRET_KEY == "dev-secret-key-change-in-production":
    _env = os.environ.get("ENV", os.environ.get("ENVIRONMENT", "development"))
    if _env.lower() in ("production", "prod"):
        raise RuntimeError(
            "FATAL: JWT_SECRET_KEY must be set in production. Do not use default secret."
        )

security = HTTPBearer(auto_error=False)


def _is_legacy_hash(hashed_password: str) -> bool:
    """Check if password hash is legacy SHA256 format (salt:hex)."""
    if ":" not in hashed_password:
        return False
    parts = hashed_password.split(":")
    return len(parts) == 2 and len(parts[0]) == 32 and len(parts[1]) == 64


def _verify_legacy_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against legacy SHA256 hash."""
    try:
        salt, stored_hash = hashed_password.split(":")
        computed_hash = hashlib.sha256((salt + plain_password).encode()).hexdigest()
        return computed_hash == stored_hash
    except ValueError:
        return False


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash (supports both bcrypt and legacy SHA256)."""
    if _is_legacy_hash(hashed_password):
        return _verify_legacy_password(plain_password, hashed_password)
    try:
        return bcrypt.checkpw(plain_password.encode(), hashed_password.encode())
    except (ValueError, TypeError):
        return False


def create_access_token(user_id: str, role: str = "user", tenant_id: Optional[str] = None) -> str:
    """Create a JWT access token."""
    expire = datetime.utcnow() + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {"sub": user_id, "role": role, "exp": expire}
    if tenant_id:
        payload["tenant_id"] = tenant_id
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    """Decode and validate a JWT token."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None


def create_user(db: Session, email: str, password: str, role: str = "user") -> User:
    """Create a new user."""
    user_id = str(uuid.uuid4())
    user = User(
        id=user_id,
        email=email.lower(),
        password_hash=hash_password(password),
        role=role
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate a user by email and password. Auto-migrates legacy SHA256 hashes to bcrypt."""
    user = db.query(User).filter(User.email == email.lower()).first()
    if not user or not verify_password(password, user.password_hash):
        return None
    # Auto-migrate legacy SHA256 hash to bcrypt on successful login
    if _is_legacy_hash(user.password_hash):
        user.password_hash = hash_password(password)
        db.commit()
    return user


def get_user_by_id(db: Session, user_id: str) -> Optional[User]:
    """Get a user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_id_and_tenant(db: Session, user_id: str, tenant_id: str) -> Optional[User]:
    """Get a user by ID within a specific tenant scope."""
    return db.query(User).filter(
        User.id == user_id,
        User.tenant_id == tenant_id
    ).first()


def get_users_by_tenant(db: Session, tenant_id: str) -> list[User]:
    """Get all users belonging to a tenant."""
    return db.query(User).filter(User.tenant_id == tenant_id).all()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user from JWT token. Returns None if no token."""
    if not credentials:
        return None

    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = get_user_by_id(db, payload.get("sub"))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


async def require_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Require authentication. Raises 401 if not authenticated."""
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")

    payload = decode_token(credentials.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")

    user = get_user_by_id(db, payload.get("sub"))
    if not user:
        raise HTTPException(status_code=401, detail="User not found")

    return user


async def require_admin(user: User = Depends(require_auth)) -> User:
    """Require admin role."""
    if user.role != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
