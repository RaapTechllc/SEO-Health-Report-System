"""Report paths and webhook columns for audits table

Revision ID: 004_report_columns
Revises: 003_progress_events
Create Date: 2025-01-18

"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op

revision: str = "004_report_columns"
down_revision: Union[str, None] = "003_progress_events"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('audits', sa.Column('report_html_path', sa.String(500), nullable=True))
    op.add_column('audits', sa.Column('report_pdf_path', sa.String(500), nullable=True))
    op.add_column('audits', sa.Column('callback_url', sa.String(500), nullable=True))
    op.add_column('audits', sa.Column('callback_delivered_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('audits', 'callback_delivered_at')
    op.drop_column('audits', 'callback_url')
    op.drop_column('audits', 'report_pdf_path')
    op.drop_column('audits', 'report_html_path')
