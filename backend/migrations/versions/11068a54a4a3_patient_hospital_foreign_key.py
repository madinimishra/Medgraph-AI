"""patient hospital foreign key

Revision ID: 11068a54a4a3
Revises: 91f7a5d8ddd1
Create Date: 2026-07-27 17:56:18.037898
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "11068a54a4a3"
down_revision: Union[str, Sequence[str], None] = "91f7a5d8ddd1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.add_column(
        "patients",
        sa.Column(
            "hospital_id",
            sa.Integer(),
            nullable=True
        )
    )

    op.create_foreign_key(
        None,
        "patients",
        "hospitals",
        ["hospital_id"],
        ["id"]
    )

    op.execute("""
        UPDATE patients
        SET hospital_id = 6
        WHERE hospital_id IS NULL;
    """)

    op.alter_column(
        "patients",
        "hospital_id",
        nullable=False
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_patients_hospital",
        "patients",
        type_="foreignkey"
    )

    op.drop_column(
        "patients",
        "hospital_id"
    )