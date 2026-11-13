"""Plain data types passed between the repository, service and controller layers.

They keep SQLAlchemy rows out of the services and templates, and HTTP request objects
out of the services and repositories. frozen=True makes them read-only, so no layer can
change what another layer sent it.
"""

from dataclasses import dataclass
from decimal import Decimal

from app.models import ResidenceArea, Sex


@dataclass(frozen=True)
class ObservationCriteria:
    """Filters for observations; ``None`` means "do not filter on this"."""

    country_iso3: str | None = None
    indicator_code: str | None = None
    region: str | None = None
    year_from: int | None = None
    year_to: int | None = None
    sex: Sex | None = None


@dataclass(frozen=True)
class ObservationListItem:
    """One entry of the observations list: an observation joined with its country
    and indicator details, ready to show."""

    country_name: str
    country_iso3: str
    region: str | None
    indicator_code: str
    indicator_name: str
    unit: str | None
    year: int
    sex: Sex
    residence_area: ResidenceArea
    value: Decimal | None


@dataclass(frozen=True)
class Option:
    """One choice in a filter drop-down list."""

    value: str
    label: str


@dataclass(frozen=True)
class FilterOptions:
    """All the lists of the filter form."""

    countries: tuple[Option, ...]
    indicators: tuple[Option, ...]
    regions: tuple[str, ...]
    sexes: tuple[Option, ...]
