"""Lab 2, Task 2.2: add the IQR outlier flag observation.is_outlier

clean_observations() flags values below Q1 - 1.5 x IQR or above Q3 + 1.5 x IQR of their
indicator; the rows are kept and marked instead of being dropped.

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0002"
down_revision: Union[str, Sequence[str], None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add observation.is_outlier (false for existing rows)."""
    op.add_column(
        "observation",
        sa.Column("is_outlier", sa.Boolean(), server_default=sa.false(), nullable=False),
    )


def downgrade() -> None:
    """Remove observation.is_outlier."""
    op.drop_column("observation", "is_outlier")
