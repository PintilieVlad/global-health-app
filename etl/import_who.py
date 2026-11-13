"""Import the WHO Global Health Observatory indicators into the database.

Needs the country table (run `python -m etl.import_worldbank` first) and the files saved
by the extraction (etl/extract_who.py). An indicator whose file is missing is skipped,
e.g. while the GHO API is unavailable.

Run from the project folder:  python -m etl.import_who
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
from etl.transform_who import transform_who_file

SOURCE = SourceSpec(
    name="WHO GHO", url="https://www.who.int/data/gho", raw_dir=RAW_ROOT / "who"
)

INDICATORS = (
    IndicatorSpec(
        code="SDGPM25",
        remote_id="SDGPM25",
        name="Concentrations of fine particulate matter (PM2.5)",
        unit="µg/m³",
        raw_filename="SDGPM25_from2000.json",
    ),
    IndicatorSpec(
        code="SDGAIRBODA",
        remote_id="SDGAIRBODA",
        name="Age-standardized death rate attributed to household and ambient air pollution",
        unit="per 100,000 population",
        raw_filename="SDGAIRBODA_from2000.json",
    ),
)


def import_all() -> list[StepResult]:
    return import_for_loaded_countries(SOURCE, INDICATORS, transform_who_file)


if __name__ == "__main__":
    configure_logging()
    report_and_exit_on_failure(import_all())
