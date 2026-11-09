"""Create or upgrade the project tables with the Alembic migrations.

Run from the project folder:  python -m app.create_tables   (same as: alembic upgrade head)

A database created in Lab 1 with Base.metadata.create_all() already has the Lab 1 tables
but no Alembic version: it is first stamped at the baseline revision 0001, so that only
the later migrations (such as the is_outlier column of Lab 2) are applied to it.
"""
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect

from app.database import engine

ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"
BASELINE_REVISION = "0001"


def main() -> None:
    config = Config(str(ALEMBIC_INI))
    tables = set(inspect(engine).get_table_names())
    if "observation" in tables and "alembic_version" not in tables:
        print(f"Lab 1 tables found without an Alembic version: stamping {BASELINE_REVISION}")
        command.stamp(config, BASELINE_REVISION)
    command.upgrade(config, "head")
    print("Database schema is at the latest migration (alembic upgrade head).")


if __name__ == "__main__":
    main()
