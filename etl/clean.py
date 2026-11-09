"""Data cleaning rules applied to every normalized table before it is stored (Lab 2, 2.3).

Raw data is never stored as it arrives. clean_observations() keeps only real countries,
standardizes the codes, converts the types, harmonizes the sex and residence-area
categories, drops missing values, fractional years, years outside the study window,
impossible values and duplicates. Every rule that removes rows goes through _drop(),
which logs how many rows were dropped and why.

The IQR outlier rule (Task 2.2) is different: outliers are kept and flagged in the
is_outlier column, because an extreme value (e.g. PM2.5 in a desert country) can be a
real measurement that the analysis needs to see.
"""
import logging
from typing import NamedTuple

import pandas as pd

from app.models import ResidenceArea, Sex

logger = logging.getLogger(__name__)

_OUTPUT_COLUMNS = [
    "country_iso3",
    "indicator_code",
    "year",
    "sex",
    "residence_area",
    "value",
    "value_low",
    "value_high",
    "is_outlier",
]
# The natural key of an observation: the uq_observation constraint in app/models.py,
# with the indicator code standing in for indicator_id.
_KEY_COLUMNS = ["country_iso3", "indicator_code", "year", "sex", "residence_area"]

# WHO GHO uses "SEX_BTSX" and "RESIDENCEAREATYPE_URB"; derived from the enums in
# app/models.py so the codes cannot drift apart.
_SEX_MAP = {f"SEX_{sex.value}": sex.value for sex in Sex}
_VALID_SEX = {sex.value for sex in Sex}
_AREA_MAP = {f"RESIDENCEAREATYPE_{area.value}": area.value for area in ResidenceArea}
_VALID_AREA = {area.value for area in ResidenceArea}

# The same country under another code: Our World in Data has no ISO code for Kosovo
# and uses OWID_KOS, the World Bank (our country table) uses XKX.
_ISO3_ALIASES = {"OWID_KOS": "XKX"}

# Task 2.2: values below Q1 - 1.5 x IQR or above Q3 + 1.5 x IQR are flagged.
IQR_FACTOR = 1.5


class _Bounds(NamedTuple):
    """Plausible value range; ``high`` is inclusive, ``low`` if ``low_inclusive``."""

    low: float
    high: float
    low_inclusive: bool = True


# PM2.5 in µg/m³: a yearly mean of exactly 0 is not a real measurement (the cleanest
# countries are around 5); 500 is far above any national yearly mean.
_PM25 = _Bounds(0, 500, low_inclusive=False)
# Deaths per 100,000 people: 1,000 per 100,000 would mean 1 % of the population
# dying of a single cause in a year.
_DEATH_RATE = _Bounds(0, 1000)
_PERCENT = _Bounds(0, 100)

# Per-indicator plausibility bounds. Values outside them are dropped before reaching
# the database.
_INDICATOR_BOUNDS = {
    "EN.ATM.PM25.MC.M3": _PM25,
    "OWID_PM25_EXPOSURE": _PM25,
    "SDGPM25": _PM25,
    "SH.STA.AIRP.P5": _DEATH_RATE,
    "OWID_CRD_DEATH_RATE": _DEATH_RATE,
    "SDGAIRBODA": _DEATH_RATE,
    "SH.PRV.SMOK": _PERCENT,
    "EG.CFT.ACCS.ZS": _PERCENT,
    # a GDP per capita of exactly 0 is not a real measurement either
    "NY.GDP.PCAP.CD": _Bounds(0, 500_000, low_inclusive=False),
}


def _drop(cleaned: pd.DataFrame, mask: pd.Series, reason: str) -> pd.DataFrame:
    """Drop the rows where ``mask`` is true, logging how many and why."""
    dropped = int(mask.sum())
    if dropped:
        logger.info("dropped %d observation rows: %s", dropped, reason)
    return cleaned[~mask]


def _out_of_bounds(cleaned: pd.DataFrame) -> pd.Series:
    mask = pd.Series(False, index=cleaned.index)
    for code, bounds in _INDICATOR_BOUNDS.items():
        value = cleaned["value"]
        too_low = value < bounds.low if bounds.low_inclusive else value <= bounds.low
        mask |= (cleaned["indicator_code"] == code) & (too_low | (value > bounds.high))
    return mask


def iqr_outliers(cleaned: pd.DataFrame, factor: float = IQR_FACTOR) -> pd.Series:
    """True where a value lies outside [Q1 - factor x IQR, Q3 + factor x IQR].

    Q1, Q3 and IQR = Q3 - Q1 are computed separately for each indicator, over all its
    countries and years.
    """
    by_indicator = cleaned.groupby("indicator_code")["value"]
    q1 = cleaned["indicator_code"].map(by_indicator.quantile(0.25))
    q3 = cleaned["indicator_code"].map(by_indicator.quantile(0.75))
    iqr = q3 - q1
    outside = (cleaned["value"] < q1 - factor * iqr) | (cleaned["value"] > q3 + factor * iqr)
    return outside.astype(bool)


def clean_observations(
    normalized: pd.DataFrame,
    valid_iso3: set[str],
    *,
    year_window: tuple[int, int] = (2000, 2024),
) -> pd.DataFrame:
    if normalized.empty:
        return pd.DataFrame(columns=_OUTPUT_COLUMNS)

    cleaned = normalized.copy()
    # World Bank and OWID tables have no residence area or uncertainty interval.
    for column in ("residence_area", "value_low", "value_high"):
        if column not in cleaned:
            cleaned[column] = None

    # Standardizing identifiers, then filtering to valid entities
    cleaned["country_iso3"] = (
        cleaned["country_iso3"].astype("string").str.strip().str.upper()
    ).replace(_ISO3_ALIASES)
    cleaned = _drop(
        cleaned,
        ~cleaned["country_iso3"].isin(valid_iso3).fillna(False).astype(bool),
        "not a known country (aggregate, region or missing code)",
    )

    # Type conversion and missing values (never stored as 0)
    cleaned["year"] = pd.to_numeric(cleaned["year"], errors="coerce")
    for column in ("value", "value_low", "value_high"):
        cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")
    cleaned = _drop(
        cleaned,
        cleaned["year"].isna() | cleaned["value"].isna(),
        "missing or non-numeric year/value",
    )
    # astype(int) would truncate 2010.5 to 2010 and overwrite the real 2010 row.
    cleaned = _drop(cleaned, cleaned["year"] % 1 != 0, "year is not a whole number")
    cleaned["year"] = cleaned["year"].astype(int)

    year_low, year_high = year_window
    cleaned = _drop(
        cleaned,
        (cleaned["year"] < year_low) | (cleaned["year"] > year_high),
        f"year outside {year_low}-{year_high}",
    )

    # Harmonizing categories: a missing sex means both sexes, a missing area the total
    cleaned["sex"] = cleaned["sex"].fillna(Sex.BOTH.value).replace(_SEX_MAP)
    cleaned = _drop(cleaned, ~cleaned["sex"].isin(_VALID_SEX), "unknown sex code")
    cleaned["residence_area"] = (
        cleaned["residence_area"].fillna(ResidenceArea.TOTAL.value).replace(_AREA_MAP)
    )
    cleaned = _drop(
        cleaned,
        ~cleaned["residence_area"].isin(_VALID_AREA),
        "unknown residence area code",
    )

    cleaned = _drop(cleaned, _out_of_bounds(cleaned), "value outside plausible bounds")

    cleaned = _drop(
        cleaned,
        cleaned.duplicated(subset=_KEY_COLUMNS, keep="last"),
        "duplicate (country, indicator, year, sex, residence area); kept the last",
    )

    # Task 2.2: flag (do not drop) the IQR outliers of each indicator
    cleaned["is_outlier"] = iqr_outliers(cleaned)
    flagged = int(cleaned["is_outlier"].sum())
    if flagged:
        logger.info(
            "flagged %d of %d observation rows as IQR outliers (kept)",
            flagged,
            len(cleaned),
        )

    return cleaned[_OUTPUT_COLUMNS]
