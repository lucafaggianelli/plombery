"""add pipeline version to runs

Revision ID: b1d4e7a90c33
Revises: 8c59645ece95
Create Date: 2026-08-07

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "b1d4e7a90c33"
down_revision: Union[str, Sequence[str], None] = "8c59645ece95"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Nullable on purpose: the runs that already exist were made with a
    # definition that was never recorded, and there is no way to guess it.
    with op.batch_alter_table("pipeline_runs") as batch_op:
        batch_op.add_column(sa.Column("pipeline_version", sa.String(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("pipeline_runs") as batch_op:
        batch_op.drop_column("pipeline_version")
