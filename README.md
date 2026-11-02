# Global Health Data Platform

A web application that imports public global health data (WHO Global Health Observatory,
World Bank, Our World in Data) into its own PostgreSQL database and serves it through a
FastAPI backend and a web interface.

**Status:** Lab 1 – environment, architecture and database. The five tables are created;
the data import comes in the next lab.

## Topic

**Air pollution and respiratory disease.** Is long-term exposure to fine particulate
matter (PM2.5) associated with higher death rates from chronic respiratory diseases
across countries, after accounting for income and smoking?

- Sources: World Bank and Our World in Data (SatPM PM2.5, WHO Mortality Database); the WHO Global Health Observatory is a backup, since its API returned HTTP 500 on 2 November 2026
- Users: public health students and analysts, environmental NGOs
- ML idea: regression of the respiratory death rate on PM2.5, GDP per capita and tobacco use

## Architecture

```
External sources (WHO GHO, World Bank, Our World in Data)
        │  HTTP requests
        ▼
Import pipeline  etl/  ──► raw file cache  data/raw/
        │  insert or update (upsert)
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
| `observation` | One value per country, indicator, year and sex (fact table) |
| `import_log` | Audit trail of every import |

Design reference: [`db/schema.sql`](db/schema.sql). SQLAlchemy models: [`app/models.py`](app/models.py).

## Setup (macOS)

Requirements: Python 3.12–3.14 and PostgreSQL 18 (Postgres.app) running on `localhost:5432`.

Once `gh_user` and `global_health` exist (Lab 1, section 1.4):

```bash
python3.14 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # only if .env is missing
python -m app.create_tables
```

The last command creates the five empty tables. Check them in pgAdmin under
global_health → Schemas → public → Tables. The schema exported with `pg_dump --schema-only`
is in [`db/schema_dump.sql`](db/schema_dump.sql).

On Windows, activate the environment with `.venv\Scripts\activate` and use `copy`
instead of `cp`. PostgreSQL can also run in Docker with `docker compose up -d`.

## Project structure

```
global-health-app/
├── .env.example          # connection string template (.env itself is not in Git)
├── requirements.txt
├── docker-compose.yml    # optional: PostgreSQL in Docker
├── db/
│   ├── schema.sql        # database design
│   └── schema_dump.sql   # schema exported from PostgreSQL (Task 1.9)
├── data/raw/             # cached downloads (not in Git)
├── etl/                  # import pipeline (Lab 2)
├── app/                  # database.py, models.py, create_tables.py; templates/ (later labs)
├── notebooks/            # data exploration
└── tests/                # tests (later labs)
```
