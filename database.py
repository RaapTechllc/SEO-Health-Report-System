"""
Database models and initialization for SEO Health Report System.
Uses SQLAlchemy with SQLite (dev) or PostgreSQL (prod).
"""

import os
from datetime import datetime

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./seo_health.db")


def _create_engine(url: str):
    """Create SQLAlchemy engine with appropriate configuration."""
    app_env = os.getenv("APP_ENV", "development").lower()
    is_production = app_env in ("production", "prod")

    if "sqlite" in url:
        if is_production:
            raise RuntimeError(
                "FATAL: SQLite is not supported in production. "
                "Set DATABASE_URL to a PostgreSQL connection string."
            )
        return create_engine(url, connect_args={"check_same_thread": False})

    # PostgreSQL connection pooling
    pool_size = int(os.getenv("DB_POOL_SIZE", "5"))
    max_overflow = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    pool_timeout = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    pool_recycle = int(os.getenv("DB_POOL_RECYCLE", "1800"))
    pool_pre_ping = os.getenv("DB_POOL_PRE_PING", "true").lower() == "true"

    return create_engine(
        url,
        pool_size=pool_size,
        max_overflow=max_overflow,
        pool_timeout=pool_timeout,
        pool_recycle=pool_recycle,
        pool_pre_ping=pool_pre_ping,
    )


engine = _create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Tenant(Base):
    __tablename__ = "tenants"

    id = Column(String(36), primary_key=True)
    name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    settings_json = Column(JSON, nullable=True)

    users = relationship("User", back_populates="tenant")
    audits = relationship("Audit", back_populates="tenant")
    payments = relationship("Payment", back_populates="tenant")
    competitors = relationship("Competitor", back_populates="tenant")
    webhooks = relationship("Webhook", back_populates="tenant")
    branding = relationship("TenantBranding", back_populates="tenant", uselist=False)
    quota = relationship("TenantQuota", back_populates="tenant", uselist=False)


class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="user")
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="users")
    audits = relationship("Audit", back_populates="user")
    payments = relationship("Payment", back_populates="user")


class Audit(Base):
    __tablename__ = "audits"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=True, index=True)
    url = Column(String(500), nullable=False)
    company_name = Column(String(255), nullable=False)
    tier = Column(String(50), default="basic")
    status = Column(String(50), default="pending", index=True)  # pending, running, completed, failed
    overall_score = Column(Integer, nullable=True)
    grade = Column(String(5), nullable=True)
    result = Column(JSON, nullable=True)
    report_path = Column(String(500), nullable=True)
    trade_type = Column(String(50), nullable=True)
    service_areas = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="audits")
    tenant = relationship("Tenant", back_populates="audits")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False, index=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=True, index=True)
    stripe_payment_intent_id = Column(String(255), unique=True, nullable=True, index=True)
    stripe_checkout_session_id = Column(String(255), unique=True, nullable=True, index=True)
    amount = Column(Integer, nullable=False)  # cents
    currency = Column(String(3), default="usd")
    tier = Column(String(50), nullable=False)
    status = Column(String(50), default="pending", index=True)  # pending, succeeded, failed
    audit_id = Column(String(36), ForeignKey("audits.id"), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="payments")
    tenant = relationship("Tenant", back_populates="payments")


class Competitor(Base):
    __tablename__ = "competitors"

    id = Column(String(36), primary_key=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=True, index=True)
    url = Column(String(500), nullable=False)
    company_name = Column(String(255), nullable=False)
    monitoring_frequency = Column(Integer, default=3600)
    alert_threshold = Column(Integer, default=10)
    last_score = Column(Integer, nullable=True)
    last_audit_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="competitors")


class TenantBranding(Base):
    """Tenant branding configuration for report customization."""
    __tablename__ = "tenant_branding"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), unique=True, nullable=False, index=True)
    logo_url = Column(String(500), nullable=True)
    primary_color = Column(String(7), default="#1E3A8A")  # hex color
    secondary_color = Column(String(7), default="#3B82F6")  # hex color
    footer_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="branding")


class TenantQuota(Base):
    """Per-tenant usage quotas and limits."""
    __tablename__ = "tenant_quotas"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), unique=True, nullable=False, index=True)

    # Monthly limits
    monthly_audits_limit = Column(Integer, default=10)  # basic=10, pro=50, enterprise=-1 (unlimited)
    monthly_audits_used = Column(Integer, default=0)
    billing_cycle_start = Column(DateTime, nullable=True)

    # Concurrent limits
    max_concurrent_audits = Column(Integer, default=2)  # basic=2, pro=5, enterprise=20

    # Per-audit limits
    max_pages_per_audit = Column(Integer, default=50)  # basic=50, pro=200, enterprise=1000
    max_ai_prompts_per_audit = Column(Integer, default=10)  # basic=10, pro=50, enterprise=200

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="quota")


class Webhook(Base):
    """Webhook subscription for event notifications."""
    __tablename__ = "webhooks"

    id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=False, index=True)
    url = Column(String(500), nullable=False)
    secret = Column(String(255), nullable=False)
    events = Column(JSON, nullable=False)  # ["audit.completed", "audit.failed"]
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    tenant = relationship("Tenant", back_populates="webhooks")
    deliveries = relationship("WebhookDelivery", back_populates="webhook", cascade="all, delete-orphan")


class WebhookDelivery(Base):
    """Tracks individual webhook delivery attempts."""
    __tablename__ = "webhook_deliveries"

    id = Column(String(36), primary_key=True)
    webhook_id = Column(String(36), ForeignKey("webhooks.id", ondelete="CASCADE"), nullable=False, index=True)
    event_type = Column(String(50), nullable=False)
    payload = Column(JSON, nullable=False)
    status = Column(String(20), default="pending", index=True)  # pending, delivered, failed
    attempts = Column(Integer, default=0)
    next_retry_at = Column(DateTime, nullable=True)
    response_code = Column(Integer, nullable=True)
    response_body = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    delivered_at = Column(DateTime, nullable=True)

    webhook = relationship("Webhook", back_populates="deliveries")



class AuditJob(Base):
    """Async audit job queue."""
    __tablename__ = "audit_jobs"

    job_id = Column(String(36), primary_key=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=True, index=True)
    audit_id = Column(String(36), ForeignKey("audits.id"), nullable=False, index=True)
    status = Column(String(50), default="queued", index=True)  # queued, processing, completed, failed
    idempotency_key = Column(String(64), unique=True, nullable=True, index=True)
    payload_json = Column(JSON, nullable=False)
    queued_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)

    tenant = relationship("Tenant")
    audit = relationship("Audit")


class CostEvent(Base):
    """
    Append-only cost ledger entry for any billable API call during an audit.
    Tracks AI provider usage, tokens, and costs for per-report cost analysis.
    """
    __tablename__ = "cost_events"

    id = Column(String(36), primary_key=True)
    audit_id = Column(String(36), ForeignKey("audits.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(String(36), ForeignKey("tenants.id"), nullable=True, index=True)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=True, index=True)

    tier = Column(String(50), nullable=True, index=True)  # low/medium/high as executed
    phase = Column(String(80), nullable=True, index=True)  # e.g., "ai_visibility", "exec_summary", "image_header"

    provider = Column(String(50), nullable=False, index=True)  # openai/google/anthropic/xai/perplexity
    model = Column(String(120), nullable=True, index=True)     # e.g., gpt-5-mini, gemini-3.0-pro
    operation = Column(String(80), nullable=False, index=True) # "chat", "image", "search", "crawl"

    # Usage accounting
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)

    # Pricing snapshot at time of call
    input_unit_cost_usd_per_1m = Column(Float, nullable=True)
    output_unit_cost_usd_per_1m = Column(Float, nullable=True)
    flat_cost_usd = Column(Float, nullable=True)

    # Final computed cost for this event
    cost_usd = Column(Float, nullable=False, default=0.0, index=True)
    currency = Column(String(8), nullable=False, default="USD")

    # Debuggable metadata (no raw prompts/responses)
    metadata_json = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    audit = relationship("Audit", backref="cost_events")


# Composite index for common queries
Index("ix_cost_events_audit_provider_model", CostEvent.audit_id, CostEvent.provider, CostEvent.model)


def init_db():
    """Create all tables."""
    Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


if __name__ == "__main__":
    init_db()
    print("Database initialized successfully!")
