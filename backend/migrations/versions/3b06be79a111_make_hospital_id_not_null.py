"""make hospital_id not null

Revision ID: 3b06be79a111
Revises: 11068a54a4a3
Create Date: 2026-07-27 18:51:16.962107
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3b06be79a111"
down_revision: Union[str, Sequence[str], None] = "11068a54a4a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "patients",
        "hospital_id",
        existing_type=sa.Integer(),
        nullable=False
    )


def downgrade() -> None:
    op.alter_column(
        "patients",
        "hospital_id",
        existing_type=sa.Integer(),
        nullable=True
    )
