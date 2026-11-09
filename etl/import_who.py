"""Import the WHO Global Health Observatory indicators into the database.

Needs the country table (run `python -m etl.import_worldbank` first) and the files saved
by the extraction (etl/extract_who.py). An indicator whose file is missing is skipped,
e.g. while the GHO API is unavailable.

Run from the project folder:  python -m etl.import_who
"""
from sqlalchemy.orm import Session

from app.database import get_engine
from etl.import_common import (
    RAW_ROOT,
    IndicatorSpec,
    configure_logging,
    countries_in_database,
    exit_if_failed,
    import_indicators,
)
from etl.transform_who import transform_who_file

RAW_DIR = RAW_ROOT / "who"
SOURCE_NAME = "WHO GHO"
SOURCE_URL = "https://www.who.int/data/gho"
# first year requested from the API (download_who_indicator(code, YEAR_FROM))
YEAR_FROM = 2000

INDICATORS = [
    IndicatorSpec(
        "SDGPM25",
        "Concentrations of fine particulate matter (PM2.5)",
        "µg/m³",
        f"SDGPM25_from{YEAR_FROM}.json",
    ),
    IndicatorSpec(
        "SDGAIRBODA",
        "Age-standardized death rate attributed to household and ambient air pollution",
        "per 100,000 population",
        f"SDGAIRBODA_from{YEAR_FROM}.json",
    ),
]


def main() -> None:
    with Session(get_engine()) as session:
        # The observation FK points at the country table, so that is the set
        # that counts (not the cached World Bank file).
        valid_iso3 = countries_in_database(session)
        failed = import_indicators(
            session,
            source_name=SOURCE_NAME,
            source_url=SOURCE_URL,
            raw_dir=RAW_DIR,
            indicators=INDICATORS,
            transform=transform_who_file,
            valid_iso3=valid_iso3,
        )

    exit_if_failed(failed)


if __name__ == "__main__":
    configure_logging()
    main()
