"""Parsing of HTML form fields and query strings, shared by the controllers.

Browsers submit an untouched <select> or <input> as an empty string, and users can edit
URLs by hand, so raw values are normalized here before they reach the service layer.
"""

from app.models import Sex


def blank_to_none(value: str | None) -> str | None:
    """``None`` for a missing or empty field, otherwise the value unchanged."""
    return value or None


def to_int_or_none(value: str | None) -> int | None:
    """The field as an int, or ``None`` if it is missing, empty or not a number.

    Lets a page ignore e.g. ``?year_from=abc`` instead of failing with HTTP 422.
    Not ``str.isdigit()``: it accepts e.g. "²", which ``int()`` then rejects.
    """
    if not value:
        return None
    try:
        return int(value)
    except ValueError:
        return None


def to_sex_or_none(value: str | None) -> Sex | None:
    """The field as a Sex code, or ``None`` if it is missing, empty or unknown.

    Lets a page ignore e.g. ``?sex=XYZ`` instead of failing with HTTP 422.
    """
    if not value:
        return None
    try:
        return Sex(value)
    except ValueError:
        return None
