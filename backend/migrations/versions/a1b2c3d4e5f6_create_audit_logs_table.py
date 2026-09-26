"""create audit_logs table

Revision ID: a1b2c3d4e5f6
Revises: 05d2d7520e2e
Create Date: 2026-09-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, Sequence[str], None] = '05d2d7520e2e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_email', sa.String(length=150), nullable=False),
        sa.Column('user_role', sa.String(length=50), nullable=False),
        sa.Column('question', sa.Text(), nullable=False),
        sa.Column('cypher', sa.Text(), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('error', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index('ix_audit_logs_user_email', 'audit_logs', ['user_email'])


def downgrade() -> None:
    op.drop_index('ix_audit_logs_user_email', table_name='audit_logs')
    op.drop_table('audit_logs')
