"""Turn a saved WHO GHO file into the normalized observation table.

Columns: country_iso3, indicator_code, year, sex, value, plus the topic extensions
residence_area, value_low and value_high (see db/schema.sql).
"""
import logging
from pathlib import Path

import pandas as pd

from etl.json_types import JsonRecord, read_json_records, require_keys

logger = logging.getLogger(__name__)

_NORMALIZED_COLUMNS = [
    "country_iso3",
    "indicator_code",
    "year",
    "sex",
    "residence_area",
    "value",
    "value_low",
    "value_high",
]
_REQUIRED_KEYS = ("SpatialDim", "TimeDim", "NumericValue")
_SEX_DIMENSION = "SEX"
_AREA_DIMENSION = "RESIDENCEAREATYPE"
# Further dimensions the observation table has no column for.
_EXTRA_DIMENSIONS = ("Dim2Type", "Dim3Type")


def _column(raw: pd.DataFrame, name: str) -> pd.Series:
    """``raw[name]``, or an all-missing column when the API left the field out."""
    if name in raw:
        return raw[name]
    return pd.Series(None, index=raw.index, dtype=object)


def transform_who_rows(rows: list[JsonRecord], code: str) -> pd.DataFrame:
    if not rows:
        return pd.DataFrame(columns=_NORMALIZED_COLUMNS)

    for row in rows:
        require_keys(row, _REQUIRED_KEYS, f"WHO {code}")

    raw = pd.DataFrame(rows)

    # Dim1 is the sex or the area of residence only when Dim1Type says so; rows split
    # by anything else (e.g. an age group), and rows with a second or third dimension,
    # do not fit the natural key of the observation table and are left out.
    dim1_type = _column(raw, "Dim1Type")
    keep = dim1_type.isna() | dim1_type.isin([_SEX_DIMENSION, _AREA_DIMENSION])
    for extra in _EXTRA_DIMENSIONS:
        keep &= _column(raw, extra).isna()
    left_out = int((~keep).sum())
    if left_out:
        logger.info("WHO %s: left out %d rows split by another dimension", code, left_out)
    raw = raw[keep]

    dim1 = _column(raw, "Dim1")
    dim1_type = _column(raw, "Dim1Type")
    return pd.DataFrame(
        {
            "country_iso3": raw["SpatialDim"],
            "indicator_code": code,
            "year": raw["TimeDim"],
            "sex": dim1.where(dim1_type == _SEX_DIMENSION),
            "residence_area": dim1.where(dim1_type == _AREA_DIMENSION),
            "value": raw["NumericValue"],
            # WHO uncertainty interval, e.g. Value "18.51 [17.13-19.80]"
            "value_low": _column(raw, "Low"),
            "value_high": _column(raw, "High"),
        },
        columns=_NORMALIZED_COLUMNS,
    )


def transform_who_file(path: Path, code: str) -> pd.DataFrame:
    rows = read_json_records(path)

    return transform_who_rows(rows, code)
