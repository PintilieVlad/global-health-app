"""Lab 1 schema: source, country, indicator, observation and import_log

The baseline revision. A database created in Lab 1 with `python -m app.create_tables`
(Base.metadata.create_all) already has these tables: mark it with `alembic stamp 0001`
instead of running this revision (app/create_tables.py does that automatically).

Revision ID: 0001
Revises:
Create Date: 2026-11-04

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0001"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create the five tables of db/schema.sql (Lab 1)."""
    op.create_table(
        "source",
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("url", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("source_id"),
        sa.UniqueConstraint("name"),
    )
    op.create_table(
        "country",
        sa.Column("iso3", sa.String(length=3), nullable=False),
        sa.Column("iso2", sa.String(length=2), nullable=True),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("region", sa.String(length=100), nullable=True),
        sa.Column("income_group", sa.String(length=50), nullable=True),
        sa.PrimaryKeyConstraint("iso3"),
    )
    op.create_table(
        "indicator",
        sa.Column("indicator_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("unit", sa.String(length=50), nullable=True),
        sa.Column("source_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["source_id"], ["source.source_id"]),
        sa.PrimaryKeyConstraint("indicator_id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "observation",
        sa.Column("observation_id", sa.BigInteger(), nullable=False),
        sa.Column("country_iso3", sa.String(length=3), nullable=False),
        sa.Column("indicator_id", sa.Integer(), nullable=False),
        sa.Column("year", sa.SmallInteger(), nullable=False),
        sa.Column("sex", sa.String(length=10), server_default="BTSX", nullable=False),
        sa.Column("residence_area", sa.String(length=10), server_default="TOTL",
                  nullable=False),
        sa.Column("value", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("value_low", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("value_high", sa.Numeric(precision=18, scale=4), nullable=True),
        sa.Column("imported_at", sa.DateTime(timezone=True), server_default=sa.text("now()"),
                  nullable=False),
        sa.ForeignKeyConstraint(["country_iso3"], ["country.iso3"]),
        sa.ForeignKeyConstraint(["indicator_id"], ["indicator.indicator_id"]),
        sa.PrimaryKeyConstraint("observation_id"),
        sa.UniqueConstraint("country_iso3", "indicator_id", "year", "sex", "residence_area",
                            name="uq_observation"),
    )
    op.create_index("ix_observation_indicator_year", "observation",
                    ["indicator_id", "year"], unique=False)
    op.create_table(
        "import_log",
        sa.Column("import_id", sa.Integer(), nullable=False),
        sa.Column("source_name", sa.String(length=100), nullable=False),
        sa.Column("indicator_code", sa.String(length=50), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("rows_loaded", sa.Integer(), nullable=False),
        sa.Column("imported_at", sa.DateTime(timezone=True), server_default=sa.text("now()"),
                  nullable=False),
        sa.PrimaryKeyConstraint("import_id"),
    )


def downgrade() -> None:
    """Drop the five tables."""
    op.drop_table("import_log")
    op.drop_index("ix_observation_indicator_year", table_name="observation")
    op.drop_table("observation")
    op.drop_table("indicator")
    op.drop_table("country")
    op.drop_table("source")
