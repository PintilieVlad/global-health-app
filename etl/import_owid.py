"""Import the Our World in Data charts into the database.

Needs the country table (run `python -m etl.import_worldbank` first) and the files saved
by the extraction (etl/extract_owid.py).

Run from the project folder:  python -m etl.import_owid
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
from etl.transform_owid import transform_owid_chart_file

RAW_DIR = RAW_ROOT / "owid"
SOURCE_NAME = "Our World in Data"
SOURCE_URL = "https://ourworldindata.org"

# chart slugs (download_owid_chart(slug) saves <slug>_full.csv)
CRD_SLUG = "chronic-respiratory-diseases-death-rate-who-mdb"
PM25_SLUG = "outdoor-air-pollution-exposure"
SLUGS = (CRD_SLUG, PM25_SLUG)

CHARTS = [
    IndicatorSpec(
        "OWID_CRD_DEATH_RATE",
        "Chronic respiratory diseases death rate, age-standardized "
        "(WHO Mortality Database)",
        "deaths per 100,000 people",
        f"{CRD_SLUG}_full.csv",
    ),
    IndicatorSpec(
        "OWID_PM25_EXPOSURE",
        "Outdoor air pollution exposure, population-weighted PM2.5 (SatPM)",
        "µg/m³",
        f"{PM25_SLUG}_full.csv",
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
            indicators=CHARTS,
            transform=transform_owid_chart_file,
            valid_iso3=valid_iso3,
        )

    exit_if_failed(failed)


if __name__ == "__main__":
    configure_logging()
    main()
