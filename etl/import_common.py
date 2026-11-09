"""The import loop shared by etl/import_worldbank.py, import_who.py and import_owid.py.

For every indicator whose raw file exists: transform -> clean -> upsert -> import_log,
one commit per indicator. Only expected errors (bad data, missing files, database
errors) are caught: they are logged with their traceback and the other indicators
continue. Any other exception is a bug and stops the script at once.
"""
import logging
from collections.abc import Callable, Iterable
from pathlib import Path
from typing import NamedTuple

import pandas as pd
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import Country
from etl.clean import clean_observations
from etl.load import (
    get_or_create_indicator,
    get_or_create_source,
    log_import,
    upsert_observations,
)
from etl.raw_files import read_source_url

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = PROJECT_ROOT / "data" / "raw"


class IndicatorSpec(NamedTuple):
    """One indicator to import: its code, name and unit, and the cached raw file."""

    code: str
    name: str
    unit: str
    filename: str


Transform = Callable[[Path, str], pd.DataFrame]


def countries_in_database(session: Session) -> set[str]:
    """The ISO3 codes of the country table: the set the observation FK accepts."""
    valid_iso3 = set(session.scalars(select(Country.iso3)))
    if not valid_iso3:
        raise SystemExit(
            "no countries in the database; run `python -m etl.import_worldbank` first"
        )
    return valid_iso3


def import_indicators(
    session: Session,
    *,
    source_name: str,
    source_url: str,
    raw_dir: Path,
    indicators: Iterable[IndicatorSpec],
    transform: Transform,
    valid_iso3: set[str],
) -> list[str]:
    """Import every indicator; return the codes of the indicators that failed."""
    source_id = get_or_create_source(session, source_name, source_url)
    session.commit()

    failed: list[str] = []
    for code, name, unit, filename in indicators:
        path = raw_dir / filename
        if not path.exists():
            print(f"{code:<22} SKIP (missing {path.name})")
            continue

        try:
            raw = transform(path, code)  # transform
            cleaned = clean_observations(raw, valid_iso3)  # clean
            indicator_id = get_or_create_indicator(session, code, name, unit, source_id)
            loaded = upsert_observations(session, cleaned, indicator_id)  # load
            log_import(session, source_name, code, read_source_url(path), loaded)
            session.commit()
            outliers = int(cleaned["is_outlier"].sum())
            print(
                f"{code:<22} raw={len(raw):>6}  clean={len(cleaned):>6}  "
                f"loaded={loaded:>6}  outliers={outliers:>5}"
            )
        except (ValueError, OSError, SQLAlchemyError):
            session.rollback()
            logger.exception("%s: import failed", code)
            failed.append(code)

    return failed


def exit_if_failed(failed: list[str]) -> None:
    """Exit with an error status (and the failed codes) if any indicator failed."""
    if failed:
        raise SystemExit(f"{len(failed)} import(s) failed: {', '.join(failed)}")


def configure_logging() -> None:
    """Show the log lines of the cleaning rules (how many rows each rule dropped)."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
