"""Data access layer: queries against a seeded PostgreSQL schema."""

from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.domain import ObservationCriteria, ObservationListItem, Option
from app.models import ResidenceArea, Sex
from app.repositories.observation_repository import ObservationRepository

ALL = ObservationCriteria()
AIR_POLLUTION_DEATHS = "SDGAIRBODA"  # seeded in tests/conftest.py
PM25 = "EN.ATM.PM25.MC.M3"


@pytest.fixture
def repository(seeded: Session) -> ObservationRepository:
    return ObservationRepository(seeded)


def _keys(items: list[ObservationListItem]) -> list[tuple]:
    return [(i.country_iso3, i.indicator_code, i.year, i.sex) for i in items]


def test_find_returns_rows_in_stable_order(repository: ObservationRepository) -> None:
    items = repository.find(ALL, limit=100, offset=0)

    # country name, year desc, indicator code, sex
    assert _keys(items) == [
        ("FRA", AIR_POLLUTION_DEATHS, 2019, Sex.BOTH),
        ("FRA", PM25, 2015, Sex.BOTH),
        ("KEN", AIR_POLLUTION_DEATHS, 2019, Sex.BOTH),
        ("KEN", PM25, 2000, Sex.BOTH),
        ("ROU", PM25, 2019, Sex.BOTH),
        ("ROU", AIR_POLLUTION_DEATHS, 2019, Sex.BOTH),
        ("ROU", AIR_POLLUTION_DEATHS, 2019, Sex.FEMALE),
        ("ROU", AIR_POLLUTION_DEATHS, 2019, Sex.MALE),
        ("ROU", AIR_POLLUTION_DEATHS, 2016, Sex.BOTH),
    ]


def test_find_joins_country_and_indicator_details(
    repository: ObservationRepository,
) -> None:
    criteria = ObservationCriteria(country_iso3="FRA", year_from=2019)

    assert repository.find(criteria, limit=100, offset=0) == [
        ObservationListItem(
            country_name="France",
            country_iso3="FRA",
            region="Europe & Central Asia",
            indicator_code=AIR_POLLUTION_DEATHS,
            indicator_name="Age-standardized death rate attributed to air pollution",
            unit="per 100,000 population",
            year=2019,
            sex=Sex.BOTH,
            residence_area=ResidenceArea.TOTAL,
            value=Decimal("18.3000"),
        )
    ]


def test_missing_value_is_none(repository: ObservationRepository) -> None:
    criteria = ObservationCriteria(country_iso3="KEN", indicator_code=PM25)

    assert [item.value for item in repository.find(criteria, limit=100, offset=0)] == [None]


@pytest.mark.parametrize(
    ("criteria", "expected_count"),
    [
        (ObservationCriteria(country_iso3="ROU"), 5),
        (ObservationCriteria(indicator_code=PM25), 3),
        (ObservationCriteria(region="Sub-Saharan Africa"), 2),
        (ObservationCriteria(year_from=2015), 8),
        (ObservationCriteria(year_to=2010), 1),
        (ObservationCriteria(country_iso3="ROU", year_from=2017, year_to=2019), 4),
        (ObservationCriteria(country_iso3="ROU", indicator_code=AIR_POLLUTION_DEATHS,
                             year_to=2016), 1),
        (ObservationCriteria(country_iso3="XXX"), 0),
        (ObservationCriteria(sex=Sex.BOTH), 7),
        (ObservationCriteria(sex=Sex.MALE, country_iso3="ROU"), 1),
    ],
)
def test_filters_apply_to_find_and_count(
    repository: ObservationRepository,
    criteria: ObservationCriteria,
    expected_count: int,
) -> None:
    items = repository.find(criteria, limit=100, offset=0)

    assert len(items) == expected_count
    assert repository.count(criteria) == expected_count
    for item in items:
        if criteria.country_iso3 is not None:
            assert item.country_iso3 == criteria.country_iso3
        if criteria.indicator_code is not None:
            assert item.indicator_code == criteria.indicator_code
        if criteria.region is not None:
            assert item.region == criteria.region
        if criteria.year_from is not None:
            assert item.year >= criteria.year_from
        if criteria.year_to is not None:
            assert item.year <= criteria.year_to
        if criteria.sex is not None:
            assert item.sex == criteria.sex


@pytest.mark.parametrize("sex", list(Sex))
def test_sex_filter_returns_only_rows_of_that_sex(
    repository: ObservationRepository, sex: Sex
) -> None:
    items = repository.find(ObservationCriteria(sex=sex), limit=100, offset=0)

    assert items  # the seed data has rows of every sex
    assert {item.sex for item in items} == {sex}
    assert repository.count(ObservationCriteria(sex=sex)) == len(items)


def test_limit_and_offset_page_through_without_gaps_or_repeats(
    repository: ObservationRepository,
) -> None:
    everything = _keys(repository.find(ALL, limit=100, offset=0))

    pages = [_keys(repository.find(ALL, limit=4, offset=offset)) for offset in (0, 4, 8)]

    assert [len(page) for page in pages] == [4, 4, 1]
    assert [key for page in pages for key in page] == everything


def test_offset_past_the_end_returns_nothing(repository: ObservationRepository) -> None:
    assert repository.find(ALL, limit=10, offset=100) == []


def test_filter_lookups_are_sorted_by_label(repository: ObservationRepository) -> None:
    assert repository.list_countries() == (
        Option("FRA", "France"),
        Option("KEN", "Kenya"),
        Option("XKX", "Kosovo"),
        Option("ROU", "Romania"),
    )
    assert repository.list_indicators() == (
        Option(AIR_POLLUTION_DEATHS, "Age-standardized death rate attributed to air pollution"),
        Option(PM25, "PM2.5 air pollution, mean annual exposure"),
    )


def test_regions_are_distinct_and_skip_missing_ones(
    repository: ObservationRepository,
) -> None:
    assert repository.list_regions() == ("Europe & Central Asia", "Sub-Saharan Africa")
