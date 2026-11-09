# Global Health Data Platform

A web application that imports public global health data (WHO Global Health Observatory,
World Bank, Our World in Data) into its own PostgreSQL database and serves it through a
FastAPI backend and a web interface.

**Status:** Lab 2 – the indicator data is downloaded, cleaned and stored with an idempotent
upsert; every import is logged and SQL checks confirm the stored data
([results](docs/lab2_results.md)). Lab 1 set up the environment, the architecture and the
five tables.

## Topic

**Air pollution and respiratory disease.** Is long-term exposure to fine particulate
matter (PM2.5) associated with higher death rates from chronic respiratory diseases
across countries, after accounting for income and smoking?

- Users: public health students and analysts, environmental NGOs
- ML idea: regression of the respiratory death rate on PM2.5, GDP per capita and tobacco use

## Data sources and indicators

| Source | Code in the database | Indicator | Unit | Raw file in `data/raw/` |
| --- | --- | --- | --- | --- |
| World Bank | `EN.ATM.PM25.MC.M3` | PM2.5 air pollution, mean annual exposure | µg/m³ | `worldbank/EN.ATM.PM25.MC.M3_2000-2024.json` |
| World Bank | `SH.STA.AIRP.P5` | Mortality rate attributed to household and ambient air pollution, age-standardized | per 100,000 population | `worldbank/SH.STA.AIRP.P5_2000-2024.json` |
| World Bank | `SH.PRV.SMOK` | Prevalence of current tobacco use | % of adults | `worldbank/SH.PRV.SMOK_2000-2024.json` |
| World Bank | `EG.CFT.ACCS.ZS` | Access to clean fuels and technologies for cooking | % of population | `worldbank/EG.CFT.ACCS.ZS_2000-2024.json` |
| World Bank | `NY.GDP.PCAP.CD` | GDP per capita | current US$ | `worldbank/NY.GDP.PCAP.CD_2000-2024.json` |
| World Bank | – | Country list (becomes the `country` table) | – | `worldbank/countries.json` |
| WHO GHO | `SDGPM25` | Concentrations of fine particulate matter (PM2.5), urban / rural / total | µg/m³ | `who/SDGPM25_from2000.json` |
| WHO GHO | `SDGAIRBODA` | Age-standardized death rate attributed to household and ambient air pollution | per 100,000 population | `who/SDGAIRBODA_from2000.json` |
| Our World in Data | `OWID_CRD_DEATH_RATE` | Chronic respiratory diseases death rate, age-standardized (WHO Mortality Database) | deaths per 100,000 people | `owid/chronic-respiratory-diseases-death-rate-who-mdb_full.csv` |
| Our World in Data | `OWID_PM25_EXPOSURE` | Outdoor air pollution exposure, population-weighted PM2.5 (SatPM) | µg/m³ | `owid/outdoor-air-pollution-exposure_full.csv` |

APIs: <https://api.worldbank.org/v2>, <https://ghoapi.azureedge.net/api> and
<https://ourworldindata.org/grapher/{chart}.csv>. The WHO GHO API answered HTTP 500 and
503 on 2–4 November 2026; while it is down, the WHO import skips its indicators and the
other sources are imported as usual.

## Architecture

```
External sources (WHO GHO, World Bank, Our World in Data)
        │  HTTP requests            etl/extract_*.py
        ▼
Raw files  data/raw/<source>/  (+ <file>.source.json: URL and download time)
        │  transform → clean        etl/transform_*.py, etl/clean.py
        ▼
Normalized, cleaned table (country, indicator, year, sex, residence area, value)
        │  insert or update (upsert)   etl/load.py, etl/import_*.py
        ▼
PostgreSQL database (own schema)  ◄── the single source of truth
        │  SQL queries
        ▼
Backend REST API  app/main.py (FastAPI, later labs)  ◄──► analysis and ML modules (later labs)
        │  JSON and HTML
        ▼
Web interface  app/templates/ (Jinja2, later labs)
```

Only the import pipeline calls external sources or writes to the database; the API,
the analysis modules and the interface only read from it.

## Database

| Table | Role |
| --- | --- |
| `source` | Where data comes from |
| `country` | Countries only (no aggregates), keyed by ISO3 |
| `indicator` | What is measured, with its unit and source |
| `observation` | One value per country, indicator, year, sex and residence area (fact table), with the IQR outlier flag `is_outlier` |
| `import_log` | Audit trail of every import (source URL, rows loaded, time) |

Design reference: [`db/schema.sql`](db/schema.sql). SQLAlchemy models:
[`app/models.py`](app/models.py). The schema is created and changed by the Alembic
migrations in [`alembic/versions/`](alembic/versions/): `0001` creates the five tables of
Lab 1, `0002` adds `observation.is_outlier` (Lab 2, Task 2.2).

## Setup from scratch

Requirements: Python 3.12–3.14, Git and PostgreSQL 16 or newer. The commands are for macOS
(Terminal); the Windows differences are noted below each step.

1. **Install and start PostgreSQL.** On macOS, install [Postgres.app](https://postgresapp.com),
   open it, click *Initialize* and add its tools to the PATH:
   ```bash
   echo 'export PATH="/Applications/Postgres.app/Contents/Versions/latest/bin:$PATH"' >> ~/.zprofile
   source ~/.zprofile
   ```
   The first time a program connects, Postgres.app asks whether to allow it: click *OK*.
   On Windows, use the installer from <https://www.postgresql.org/download/windows/>.
   Alternative: PostgreSQL in Docker with `docker compose up -d` (it creates the user and
   the database of step 3 itself).

2. **Get the code:**
   ```bash
   git clone https://github.com/PintilieVlad/global-health-app.git
   cd global-health-app
   ```

3. **Create the project user and database** (once):
   ```bash
   psql -d postgres -c "CREATE USER gh_user WITH PASSWORD 'gh_pass';"
   psql -d postgres -c "CREATE DATABASE global_health OWNER gh_user ENCODING 'UTF8';"
   ```
   On Windows add `-U postgres -h localhost` (the password of the `postgres` user is asked).

4. **Create the virtual environment and install the dependencies:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```
   On Windows: `python -m venv .venv` and `.venv\Scripts\activate`.

5. **Configure the connection:** copy `.env.example` to `.env` (`copy` on Windows). If you
   chose another password in step 3, change it in `DATABASE_URL` in `.env`. The `.env`
   file stays on your computer and is never committed.
   ```bash
   cp .env.example .env
   ```

6. **Create the tables** (runs the Alembic migrations; a database created in Lab 1 is
   upgraded and keeps its data):
   ```bash
   python -m app.create_tables
   ```
   Same as `alembic upgrade head`. Check with `alembic current`, which prints `0002 (head)`.

All the commands below are run from the project folder with the virtual environment
active (`source .venv/bin/activate`) and PostgreSQL running.

## Extracting the data

The extractors only download the data and save the raw response, unchanged, in
`data/raw/who/`, `data/raw/worldbank/` and `data/raw/owid/`. Next to each file, a
`<file>.source.json` records the request URL and the download time. The extractors have no
command of their own: run them from the project folder in a Python shell or a notebook.

The notebook [`notebooks/lab2_exploration.ipynb`](notebooks/lab2_exploration.ipynb)
(Task 2.1) calls every extractor and inspects the result. Open it in VS Code or Jupyter
and run all cells, or run it from the terminal (about a minute):

```bash
jupyter nbconvert --to notebook --execute --inplace notebooks/lab2_exploration.ipynb
```

The same downloads from a Python shell (`python`, started in the project folder):

```python
from etl.extract_owid import download_owid_chart
from etl.extract_who import download_who_indicator
from etl.extract_worldbank import download_worldbank_countries, download_worldbank_indicator

download_worldbank_countries()
for code in ("EN.ATM.PM25.MC.M3", "SH.STA.AIRP.P5", "SH.PRV.SMOK",
             "EG.CFT.ACCS.ZS", "NY.GDP.PCAP.CD"):
    download_worldbank_indicator(code)            # years 2000:2024
for code in ("SDGPM25", "SDGAIRBODA"):
    download_who_indicator(code)                  # from 2000
for slug in ("chronic-respiratory-diseases-death-rate-who-mdb",
             "outdoor-air-pollution-exposure"):
    download_owid_chart(slug)
```

Each function returns the path of the saved file and the request URL. A source that cannot
be reached raises an error: `requests.HTTPError`, `WhoApiError` or `WorldBankApiError`.
Every extractor also has a `*_for_year()` variant that downloads a single year. The
downloaded files are not committed (`data/raw/` is in `.gitignore`).

## Importing the data

Run the World Bank import first: it loads the `country` table, and the WHO and OWID imports
take the list of valid countries from it.

```bash
python -m etl.import_worldbank
python -m etl.import_who
python -m etl.import_owid
```

For every indicator the import transforms the saved file (`etl/transform_*.py`), cleans it (`etl/clean.py`), upserts it
(`etl/load.py`) and writes a row to `import_log`. It prints one line per indicator, together
with the log lines of the cleaning rules:

```
== World Bank
countries: 217 upserted
INFO etl.clean: dropped 1225 observation rows: not a known country (aggregate, region or missing code)
INFO etl.clean: dropped 625 observation rows: missing or non-numeric year/value
INFO etl.clean: flagged 197 of 4800 observation rows as IQR outliers (kept)
EN.ATM.PM25.MC.M3      raw=  6650  clean=  4800  loaded=  4800  outliers=  197
...
== WHO GHO
SDGPM25                SKIP (missing SDGPM25_from2000.json)
```

(from the run of 4 November 2026). `SKIP` means the raw file is missing: run the
extraction first.
The imports can be run again at any time: the upsert (`INSERT ... ON CONFLICT DO UPDATE` on
country, indicator, year, sex and residence area) updates the existing rows instead of
creating duplicates.

### Cleaning rules (`etl/clean.py`)

| Rule | What it does |
| --- | --- |
| Valid entities | keeps only codes that are in the `country` table (drops `WLD`, `OWID_EUR`, ...) |
| Standard identifiers | trims and upper-cases codes; maps OWID's `OWID_KOS` to `XKX` (Kosovo) |
| Type conversion | `pd.to_numeric(..., errors="coerce")` for year, value and the uncertainty interval |
| Missing values | drops rows with a missing year or value (never stored as 0) |
| Whole years | drops fractional years before the conversion to `int` |
| Year window | keeps 2000–2024 |
| Categories | `SEX_*` codes to `BTSX`/`MLE`/`FMLE` (missing: `BTSX`); `RESIDENCEAREATYPE_*` to `TOTL`/`URB`/`RUR` (missing: `TOTL`); unknown codes dropped |
| Range checks | per-indicator bounds: PM2.5 in (0, 500], death rates in [0, 1000], percentages in [0, 100], GDP per capita in (0, 500,000] |
| Duplicates | one row per natural key, the last one kept |
| IQR outliers | flags (does not drop) values outside [Q1 − 1.5 × IQR, Q3 + 1.5 × IQR] of their indicator in `is_outlier` |

## Checking the stored data

[`db/quality_checks.sql`](db/quality_checks.sql) holds the overview queries and the data
quality checks of section 2.5, each with its expected result. Run them in pgAdmin: open the
file in the Query Tool on `global_health` and run one query at a time. Or run them all in
the terminal:

```bash
psql -h localhost -U gh_user -d global_health -f db/quality_checks.sql
```

The results of Lab 2 and their explanation are in [`docs/lab2_results.md`](docs/lab2_results.md).

## Project structure

```
global-health-app/
├── .env.example          # connection string template (.env itself is not in Git)
├── requirements.txt
├── docker-compose.yml    # optional: PostgreSQL in Docker
├── alembic.ini, alembic/ # database migrations (0001 Lab 1 tables, 0002 is_outlier)
├── db/
│   ├── schema.sql          # database design reference
│   ├── schema_dump.sql     # schema exported from PostgreSQL (Lab 1)
│   └── quality_checks.sql  # overview queries and data quality checks
├── data/raw/             # downloaded raw files (not in Git)
├── etl/                  # import pipeline
│   ├── extract_who.py, extract_worldbank.py, extract_owid.py      # download
│   ├── transform_who.py, transform_worldbank.py, transform_owid.py  # normalize
│   ├── clean.py          # cleaning rules and the IQR outlier flag
│   ├── load.py           # upserts and import_log
│   ├── import_worldbank.py, import_who.py, import_owid.py          # one import per source
│   ├── import_common.py  # the import loop shared by the three scripts
│   └── json_types.py, raw_files.py
├── app/                  # database.py, models.py, create_tables.py; templates/ (later labs)
├── notebooks/lab2_exploration.ipynb   # Task 2.1
├── docs/
│   ├── lab2_results.md   # Tasks 2.2–2.4
│   └── prompts/lab2.md   # prompts sent to the AI assistant
└── tests/                # tests (later labs)
```
