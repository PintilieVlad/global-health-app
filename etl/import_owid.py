"""Import the Our World in Data charts into the database.

Needs the country table (run `python -m etl.import_worldbank` first) and the files saved
by the extraction (etl/extract_owid.py).

Run from the project folder:  python -m etl.import_owid
"""
from etl.import_runner import (
    RAW_ROOT,
    IndicatorSpec,
    SourceSpec,
    configure_logging,
    import_for_loaded_countries,
    report_and_exit_on_failure,
)
from etl.step_result import StepResult
from etl.transform_owid import transform_owid_chart_file

SOURCE = SourceSpec(
    name="Our World in Data",
    url="https://ourworldindata.org",
    raw_dir=RAW_ROOT / "owid",
)

INDICATORS = (
    IndicatorSpec(
        code="OWID_CRD_DEATH_RATE",
        remote_id="chronic-respiratory-diseases-death-rate-who-mdb",
        name="Chronic respiratory diseases death rate, age-standardized "
        "(WHO Mortality Database)",
        unit="deaths per 100,000 people",
        raw_filename="chronic-respiratory-diseases-death-rate-who-mdb_full.csv",
    ),
    IndicatorSpec(
        code="OWID_PM25_EXPOSURE",
        remote_id="outdoor-air-pollution-exposure",
        name="Outdoor air pollution exposure, population-weighted PM2.5 (SatPM)",
        unit="µg/m³",
        raw_filename="outdoor-air-pollution-exposure_full.csv",
    ),
)


def import_all() -> list[StepResult]:
    return import_for_loaded_countries(SOURCE, INDICATORS, transform_owid_chart_file)


if __name__ == "__main__":
    configure_logging()
    report_and_exit_on_failure(import_all())
