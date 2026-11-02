"""Create the project tables in PostgreSQL.

Run from the project folder:  python -m app.create_tables
In later labs, Alembic migrations replace create_all so schema changes are versioned.
"""
from app.database import engine
from app.models import Base

if __name__ == "__main__":
    Base.metadata.create_all(engine)
    print("Tables created:", ", ".join(Base.metadata.tables))
