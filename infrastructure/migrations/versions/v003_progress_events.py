"""Progress events table for audit status tracking

Revision ID: 003_progress_events
Revises: 002_audit_jobs
Create Date: 2025-01-18

"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "003_progress_events"
down_revision: Union[str, None] = "002_audit_jobs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "audit_progress_events",
        sa.Column("event_id", sa.String(36), primary_key=True),
        sa.Column("audit_id", sa.String(36), sa.ForeignKey("audits.id"), nullable=False),
        sa.Column("job_id", sa.String(36), sa.ForeignKey("audit_jobs.job_id"), nullable=True),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("message", sa.Text, nullable=True),
        sa.Column("data_json", sa.Text, nullable=True),
        sa.Column("progress_pct", sa.SmallInteger, nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "event_type IN ('status_changed', 'step_started', 'step_done', 'warning', 'error', 'metric')",
            name="ck_event_type_valid"
        ),
        sa.CheckConstraint(
            "progress_pct IS NULL OR (progress_pct >= 0 AND progress_pct <= 100)",
            name="ck_progress_pct_range"
        ),
    )

    op.create_index(
        "idx_events_audit_timeline",
        "audit_progress_events",
        ["audit_id", "created_at"]
    )


def downgrade() -> None:
    op.drop_index("idx_events_audit_timeline", table_name="audit_progress_events")
    op.drop_table("audit_progress_events")
