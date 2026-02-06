"""Audit jobs table for async job processing

Revision ID: 002_audit_jobs
Revises: 001_initial_schema
Create Date: 2025-01-18
"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "002_audit_jobs"
down_revision: Union[str, None] = "001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "tenants",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
    )

    op.create_table(
        "audit_jobs",
        sa.Column("job_id", sa.String(36), primary_key=True),
        sa.Column("tenant_id", sa.String(36), sa.ForeignKey("tenants.id"), nullable=False),
        sa.Column("audit_id", sa.String(36), sa.ForeignKey("audits.id"), nullable=False),

        # State machine
        sa.Column("status", sa.String(20), nullable=False, server_default="queued"),

        # Retry handling
        sa.Column("attempt", sa.Integer, nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer, nullable=False, server_default="3"),

        # Timestamps
        sa.Column("queued_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("started_at", sa.DateTime, nullable=True),
        sa.Column("finished_at", sa.DateTime, nullable=True),

        # Lease management
        sa.Column("locked_until", sa.DateTime, nullable=True),
        sa.Column("locked_by", sa.String(255), nullable=True),

        # Idempotency
        sa.Column("idempotency_key", sa.String(64), nullable=False, unique=True),

        # Payload
        sa.Column("payload_json", sa.Text, nullable=False),

        # Error tracking
        sa.Column("last_error", sa.Text, nullable=True),

        # Status constraint
        sa.CheckConstraint(
            "status IN ('queued', 'running', 'done', 'failed', 'canceled')",
            name="ck_audit_jobs_status"
        ),
    )

    # Index for tenant lookups
    op.create_index("idx_jobs_tenant", "audit_jobs", ["tenant_id", "queued_at"])

    # Index for job claiming (non-partial for SQLite compatibility)
    op.create_index("idx_jobs_status_queued", "audit_jobs", ["status", "queued_at"])


def downgrade() -> None:
    op.drop_index("idx_jobs_status_queued", table_name="audit_jobs")
    op.drop_index("idx_jobs_tenant", table_name="audit_jobs")
    op.drop_table("audit_jobs")
    op.drop_table("tenants")
