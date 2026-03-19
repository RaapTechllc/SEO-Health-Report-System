"""Add tenant_quotas table for per-tenant usage limits

Revision ID: 007_tenant_quotas
Revises: 006_tenant_branding
Create Date: 2025-01-18

"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "007_tenant_quotas"
down_revision: Union[str, None] = "006_tenant_branding"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'tenant_quotas',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id'), nullable=False, unique=True, index=True),
        # Monthly limits
        sa.Column('monthly_audits_limit', sa.Integer(), default=10),
        sa.Column('monthly_audits_used', sa.Integer(), default=0),
        sa.Column('billing_cycle_start', sa.DateTime(), nullable=True),
        # Concurrent limits
        sa.Column('max_concurrent_audits', sa.Integer(), default=2),
        # Per-audit limits
        sa.Column('max_pages_per_audit', sa.Integer(), default=50),
        sa.Column('max_ai_prompts_per_audit', sa.Integer(), default=10),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('tenant_quotas')
