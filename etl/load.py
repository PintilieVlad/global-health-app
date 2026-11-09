"""Store cleaned data in PostgreSQL: idempotent upserts and the import log (Lab 2, 2.4).

INSERT ... ON CONFLICT DO UPDATE on the natural key means that running an import twice
updates the existing rows instead of creating duplicates.
"""
import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session

from app.models import Country, ImportLog, Indicator, Observation, Source

# Columns refreshed when an observation already exists (the key columns stay as they are).
_UPDATED_COLUMNS = ("value", "value_low", "value_high", "is_outlier")


def _records(frame: pd.DataFrame) -> list[dict[str, object]]:
    """Rows as dicts with missing values as None.

    pandas marks missing values with NaN, which PostgreSQL would store in a NUMERIC
    column as the special value 'NaN' instead of NULL.
    """
    return frame.astype(object).where(frame.notna(), None).to_dict("records")


def get_or_create_source(session: Session, name: str, url: str) -> int:
    source = session.scalar(select(Source).where(Source.name == name))
    if source is None:
        source = Source(name=name, url=url)
        session.add(source)
        session.flush()

    return source.source_id


def get_or_create_indicator(
    session: Session, code: str, name: str, unit: str, source_id: int
) -> int:
    indicator = session.scalar(select(Indicator).where(Indicator.code == code))
    if indicator is None:
        indicator = Indicator(code=code, name=name, unit=unit, source_id=source_id)
        session.add(indicator)
        session.flush()

    return indicator.indicator_id


def upsert_countries(session: Session, countries: pd.DataFrame) -> None:
    if countries.empty:
        return

    stmt = insert(Country).values(_records(countries))
    stmt = stmt.on_conflict_do_update(
        index_elements=["iso3"],
        set_={
            col: stmt.excluded[col]
            for col in ("iso2", "name", "region", "income_group")
        },
    )
    session.execute(stmt)


def upsert_observations(
    session: Session,
    observations: pd.DataFrame,
    indicator_id: int,
    chunk_size: int = 5000,
) -> int:
    """Insert or update the observations of one indicator; return the number of rows."""
    if observations.empty:
        return 0

    # observation table has indicator_id (FK), not indicator_code (string)
    rows = _records(
        observations.drop(columns=["indicator_code"]).assign(indicator_id=indicator_id)
    )
    for start in range(0, len(rows), chunk_size):
        stmt = insert(Observation).values(rows[start : start + chunk_size])
        stmt = stmt.on_conflict_do_update(
            constraint="uq_observation",
            set_={
                **{col: stmt.excluded[col] for col in _UPDATED_COLUMNS},
                "imported_at": func.now(),
            },
        )
        session.execute(stmt)

    return len(rows)


def log_import(
    session: Session,
    source_name: str,
    indicator_code: str,
    url: str,
    rows_loaded: int,
) -> None:
    session.add(
        ImportLog(
            source_name=source_name,
            indicator_code=indicator_code,
            url=url,
            rows_loaded=rows_loaded,
        )
    )
