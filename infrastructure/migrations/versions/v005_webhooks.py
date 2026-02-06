"""Add webhooks and webhook_deliveries tables

Revision ID: 005_webhooks
Revises: 004_report_columns
Create Date: 2025-01-18

"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "005_webhooks"
down_revision: Union[str, None] = "004_report_columns"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'webhooks',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('tenant_id', sa.String(36), sa.ForeignKey('tenants.id'), nullable=False, index=True),
        sa.Column('url', sa.String(500), nullable=False),
        sa.Column('secret', sa.String(255), nullable=False),
        sa.Column('events', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
    )

    op.create_table(
        'webhook_deliveries',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('webhook_id', sa.String(36), sa.ForeignKey('webhooks.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('event_type', sa.String(50), nullable=False),
        sa.Column('payload', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(20), default='pending', index=True),
        sa.Column('attempts', sa.Integer(), default=0),
        sa.Column('next_retry_at', sa.DateTime(), nullable=True),
        sa.Column('response_code', sa.Integer(), nullable=True),
        sa.Column('response_body', sa.Text(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('webhook_deliveries')
    op.drop_table('webhooks')
