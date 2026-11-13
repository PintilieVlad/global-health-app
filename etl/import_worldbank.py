"""Import the country list and the World Bank indicators into the database.

Run it before the WHO and OWID imports: it loads the country table, and they take the
list of valid countries from that table. Reads the files saved by the extraction
(etl/extract_worldbank.py), so run the extraction first.

Run from the project folder:  python -m etl.import_worldbank
"""
import logging

from sqlalchemy.orm import Session

from app.database import get_engine
from etl.extract_worldbank import DEFAULT_YEARS
from etl.import_runner import (
    IMPORT_ERRORS,
    RAW_ROOT,
    IndicatorSpec,
    SourceSpec,
    configure_logging,
    import_indicators,
    report_and_exit_on_failure,
)
from etl.load import upsert_countries
from etl.step_result import StepResult
from etl.transform_worldbank import (
    transform_worldbank_country_file,
    transform_worldbank_indicator_file,
)

logger = logging.getLogger(__name__)

SOURCE = SourceSpec(
    name="World Bank",
    url="https://data.worldbank.org",
    raw_dir=RAW_ROOT / "worldbank",
)
COUNTRIES_FILENAME = "countries.json"


def _indicator(code: str, name: str, unit: str) -> IndicatorSpec:
    # Matches the file name written by extract_worldbank's default year range.
    return IndicatorSpec(
        code=code,
        remote_id=code,
        name=name,
        unit=unit,
        raw_filename=f"{code}_{DEFAULT_YEARS.replace(':', '-')}.json",
    )


INDICATORS = (
    _indicator("EN.ATM.PM25.MC.M3", "PM2.5 air pollution, mean annual exposure", "µg/m³"),
    _indicator(
        "SH.STA.AIRP.P5",
        "Mortality rate attributed to household and ambient air pollution, "
        "age-standardized",
        "per 100,000 population",
    ),
    _indicator("SH.PRV.SMOK", "Prevalence of current tobacco use", "% of adults"),
    _indicator(
        "EG.CFT.ACCS.ZS",
        "Access to clean fuels and technologies for cooking",
        "% of population",
    ),
    _indicator("NY.GDP.PCAP.CD", "GDP per capita", "current US$"),
)


def _import_countries(session: Session) -> tuple[StepResult, set[str]]:
    """Load the country dimension; return the result and the ISO3 codes loaded."""
    path = SOURCE.raw_dir / COUNTRIES_FILENAME
    if not path.exists():
        message = f"missing {path.name}; run Extract first"
        return StepResult.failed(SOURCE.name, "countries", message), set()

    try:
        countries = transform_worldbank_country_file(path)
        upsert_countries(session, countries)
        session.commit()
    except IMPORT_ERRORS as error:
        session.rollback()
        logger.exception("%s countries: import failed", SOURCE.name)
        return StepResult.from_error(SOURCE.name, "countries", error), set()

    message = f"{len(countries)} upserted"
    return StepResult.ok(SOURCE.name, "countries", message), set(countries["iso3"])


def import_all() -> list[StepResult]:
    with Session(get_engine()) as session:
        countries_result, known_countries = _import_countries(session)
        if not known_countries:
            return [countries_result]

        return [countries_result] + import_indicators(
            session,
            SOURCE,
            INDICATORS,
            transform_worldbank_indicator_file,
            known_countries,
        )


if __name__ == "__main__":
    configure_logging()
    report_and_exit_on_failure(import_all())
