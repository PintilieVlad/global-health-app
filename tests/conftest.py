"""Shared fixtures.

Database tests run against real PostgreSQL (the queries are PostgreSQL-specific), but
never against the application's data: a throwaway schema is created for the test
session and dropped at the end, and every test runs inside a transaction that is rolled
back. The database comes from ``TEST_DATABASE_URL`` or, if that is not set,
``DATABASE_URL``; the user only needs to own the database, not to be able to create new
ones. Without a reachable database, the database tests are skipped.
"""

import os
from collections.abc import Iterator
from decimal import Decimal
from uuid import uuid4

import pytest
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_etl_service
from app.main import app
from app.models import Base, Country, Indicator, Observation, Sex, Source


def _no_database() -> Iterator[Session]:
    raise AssertionError("this test used the database without the db_session fixture")
    yield  # pragma: no cover - makes this a generator dependency like get_db


def _no_real_etl() -> None:
    raise AssertionError("this test ran the real ETL; override get_etl_service")


@pytest.fixture
def client() -> Iterator[TestClient]:
    """A test client that can reach neither the database nor the real ETL."""
    app.dependency_overrides[get_db] = _no_database
    app.dependency_overrides[get_etl_service] = _no_real_etl
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


CONNECT_TIMEOUT_S = 3
_unreachable_database: list[str] = []


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    load_dotenv()
    url = os.environ.get("TEST_DATABASE_URL") or os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip("set TEST_DATABASE_URL or DATABASE_URL to run the database tests")

    if _unreachable_database:
        pytest.skip(_unreachable_database[0])

    schema = f"test_{uuid4().hex[:12]}"
    admin = create_engine(url, connect_args={"connect_timeout": CONNECT_TIMEOUT_S})
    try:
        with admin.begin() as connection:
            connection.execute(text(f'CREATE SCHEMA "{schema}"'))
    except OperationalError as error:
        admin.dispose()
        # pytest retries a failed session fixture for every test; remember the failure
        # so the run does not wait for a timeout once per test.
        _unreachable_database.append(f"PostgreSQL is not reachable: {error.orig}")
        pytest.skip(_unreachable_database[0])

    test_engine = create_engine(url, connect_args={"options": f"-csearch_path={schema}"})
    try:
        Base.metadata.create_all(test_engine)
        yield test_engine
    finally:
        test_engine.dispose()
        with admin.begin() as connection:
            connection.execute(text(f'DROP SCHEMA "{schema}" CASCADE'))
        admin.dispose()


@pytest.fixture
def db_session(engine: Engine) -> Iterator[Session]:
    """A session whose work is rolled back after the test."""
    connection = engine.connect()
    transaction = connection.begin()
    session = Session(bind=connection, join_transaction_mode="create_savepoint")
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def client_with_db(client: TestClient, db_session: Session) -> TestClient:
    """The test client, with requests using the rolled-back test session."""

    def test_session() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = test_session
    return client


AIR_POLLUTION_DEATHS = "SDGAIRBODA"
PM25 = "EN.ATM.PM25.MC.M3"

# (iso3, indicator code, year, sex, value) for the seeded observations. Invented test
# values, in the range of the real indicators.
SEED_OBSERVATIONS = [
    ("ROU", AIR_POLLUTION_DEATHS, 2019, Sex.BOTH, Decimal("67.8")),
    ("ROU", AIR_POLLUTION_DEATHS, 2019, Sex.MALE, Decimal("89.5")),
    ("ROU", AIR_POLLUTION_DEATHS, 2019, Sex.FEMALE, Decimal("52.1")),
    ("ROU", AIR_POLLUTION_DEATHS, 2016, Sex.BOTH, Decimal("70.3")),
    ("ROU", PM25, 2019, Sex.BOTH, Decimal("16.4")),
    ("FRA", AIR_POLLUTION_DEATHS, 2019, Sex.BOTH, Decimal("18.3")),
    ("FRA", PM25, 2015, Sex.BOTH, Decimal("11.2")),
    ("KEN", AIR_POLLUTION_DEATHS, 2019, Sex.BOTH, Decimal("69.1")),
    ("KEN", PM25, 2000, Sex.BOTH, None),
]


@pytest.fixture
def seeded(db_session: Session) -> Session:
    """Three countries in two regions (plus one without a region), two indicators,
    nine observations."""
    source = Source(name="Test source", url="https://example.org")
    db_session.add(source)
    db_session.add_all(
        [
            Country(iso3="ROU", iso2="RO", name="Romania",
                    region="Europe & Central Asia", income_group="High income"),
            Country(iso3="FRA", iso2="FR", name="France",
                    region="Europe & Central Asia", income_group="High income"),
            Country(iso3="KEN", iso2="KE", name="Kenya",
                    region="Sub-Saharan Africa", income_group="Lower middle income"),
            Country(iso3="XKX", iso2="XK", name="Kosovo",
                    region=None, income_group=None),
        ]
    )
    db_session.flush()
    indicators = {
        AIR_POLLUTION_DEATHS: Indicator(
            code=AIR_POLLUTION_DEATHS,
            name="Age-standardized death rate attributed to air pollution",
            unit="per 100,000 population",
            source_id=source.source_id,
        ),
        PM25: Indicator(
            code=PM25,
            name="PM2.5 air pollution, mean annual exposure",
            unit="µg/m³",
            source_id=source.source_id,
        ),
    }
    db_session.add_all(indicators.values())
    db_session.flush()
    db_session.add_all(
        Observation(
            country_iso3=iso3,
            indicator_id=indicators[code].indicator_id,
            year=year,
            sex=sex,
            value=value,
        )
        for iso3, code, year, sex, value in SEED_OBSERVATIONS
    )
    db_session.flush()

    return db_session
