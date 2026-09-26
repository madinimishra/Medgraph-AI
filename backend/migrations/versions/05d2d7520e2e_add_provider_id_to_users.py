"""add provider_id to users

Revision ID: 05d2d7520e2e
Revises: 3c22febfc687
Create Date: 2026-09-05 17:15:09.732618

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '05d2d7520e2e'
down_revision: Union[str, Sequence[str], None] = '3c22febfc687'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('provider_id', sa.String(length=100), nullable=True))


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'provider_id')
