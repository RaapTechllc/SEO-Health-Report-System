"""Add trade_type and service_areas columns to audits table

Revision ID: 007_audit_trade_fields
Revises: 006_tenant_branding
Create Date: 2025-01-18

Trade types supported: Plumber, Electrician, HVAC, Roofer, General Contractor, Landscaper, Painter, Other
"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "007_audit_trade_fields"
down_revision: Union[str, None] = "006_tenant_branding"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column('audits', sa.Column('trade_type', sa.String(50), nullable=True))
    op.add_column('audits', sa.Column('service_areas', sa.JSON(), nullable=True))

def downgrade() -> None:
    op.drop_column('audits', 'service_areas')
    op.drop_column('audits', 'trade_type')
