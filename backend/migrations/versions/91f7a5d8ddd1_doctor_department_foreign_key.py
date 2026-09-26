"""doctor department foreign key

Revision ID: 91f7a5d8ddd1
Revises: 7349c7cc195d
Create Date: 2026-07-27 02:38:51.622918

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '91f7a5d8ddd1'
down_revision: Union[str, Sequence[str], None] = '7349c7cc195d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add department_id as nullable first
    op.add_column(
        "doctors",
        sa.Column("department_id", sa.Integer(), nullable=True)
    )

    # Create foreign key
    op.create_foreign_key(
        "fk_doctors_department",
        "doctors",
        "departments",
        ["department_id"],
        ["id"]
    )

    # Keep the old department column for now.
    # We will remove it after migrating existing doctor data.


def downgrade() -> None:

    op.drop_constraint(
        "fk_doctors_department",
        "doctors",
        type_="foreignkey"
    )

    op.drop_column(
        "doctors",
        "department_id"
    )
