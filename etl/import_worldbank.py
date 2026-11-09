"""Import the country list and the World Bank indicators into the database.

Run it before the WHO and OWID imports: it loads the country table, and they take the
list of valid countries from that table. Reads the files saved by the extraction
(etl/extract_worldbank.py), so run the extraction first.

Run from the project folder:  python -m etl.import_worldbank
"""
from sqlalchemy.orm import Session

from app.database import get_engine
from etl.import_common import (
    PROJECT_ROOT,
    RAW_ROOT,
    IndicatorSpec,
    configure_logging,
    exit_if_failed,
    import_indicators,
)
from etl.load import upsert_countries
from etl.transform_worldbank import (
    transform_worldbank_country_file,
    transform_worldbank_indicator_file,
)

RAW_DIR = RAW_ROOT / "worldbank"
SOURCE_NAME = "World Bank"
SOURCE_URL = "https://data.worldbank.org"
# years requested from the API (download_worldbank_indicator(code, YEARS))
YEARS = "2000:2024"
_SUFFIX = YEARS.replace(":", "-")

INDICATORS = [
    IndicatorSpec(
        "EN.ATM.PM25.MC.M3",
        "PM2.5 air pollution, mean annual exposure",
        "µg/m³",
        f"EN.ATM.PM25.MC.M3_{_SUFFIX}.json",
    ),
    IndicatorSpec(
        "SH.STA.AIRP.P5",
        "Mortality rate attributed to household and ambient air pollution, "
        "age-standardized",
        "per 100,000 population",
        f"SH.STA.AIRP.P5_{_SUFFIX}.json",
    ),
    IndicatorSpec(
        "SH.PRV.SMOK",
        "Prevalence of current tobacco use",
        "% of adults",
        f"SH.PRV.SMOK_{_SUFFIX}.json",
    ),
    IndicatorSpec(
        "EG.CFT.ACCS.ZS",
        "Access to clean fuels and technologies for cooking",
        "% of population",
        f"EG.CFT.ACCS.ZS_{_SUFFIX}.json",
    ),
    IndicatorSpec(
        "NY.GDP.PCAP.CD",
        "GDP per capita",
        "current US$",
        f"NY.GDP.PCAP.CD_{_SUFFIX}.json",
    ),
]


def main() -> None:
    countries_file = RAW_DIR / "countries.json"
    if not countries_file.exists():
        raise SystemExit(
            f"missing {countries_file.relative_to(PROJECT_ROOT)}; "
            "run the extraction first (see README.md, Extracting the data)"
        )

    with Session(get_engine()) as session:
        countries = transform_worldbank_country_file(countries_file)
        upsert_countries(session, countries)
        session.commit()
        print(f"countries: {len(countries)} upserted")

        failed = import_indicators(
            session,
            source_name=SOURCE_NAME,
            source_url=SOURCE_URL,
            raw_dir=RAW_DIR,
            indicators=INDICATORS,
            transform=transform_worldbank_indicator_file,
            valid_iso3=set(countries["iso3"]),
        )

    exit_if_failed(failed)


if __name__ == "__main__":
    configure_logging()
    main()
