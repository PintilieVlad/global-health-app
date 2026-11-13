"""Service layer for browsing observations: paging rules and filter choices."""

import math
from dataclasses import dataclass

from app.domain import FilterOptions, ObservationCriteria, ObservationListItem, Option
from app.models import Sex
from app.repositories.observation_repository import ObservationRepository

DEFAULT_PAGE_SIZE = 50

# The sex filter offers the three codes of the Sex enum; they are fixed, not read from
# the database.
SEX_LABELS = {Sex.BOTH: "Both sexes", Sex.MALE: "Male", Sex.FEMALE: "Female"}


@dataclass(frozen=True)
class ObservationPage:
    """One page of observations, with what the view needs to show the navigation."""

    items: list[ObservationListItem]
    number: int
    size: int
    total_items: int

    @property
    def total_pages(self) -> int:
        # An empty result is still shown as "page 1 of 1".
        return max(1, math.ceil(self.total_items / self.size))

    @property
    def has_previous(self) -> bool:
        return self.number > 1

    @property
    def has_next(self) -> bool:
        return self.number < self.total_pages


class ObservationService:
    def __init__(
        self, repository: ObservationRepository, page_size: int = DEFAULT_PAGE_SIZE
    ) -> None:
        if page_size < 1:
            raise ValueError(f"page_size must be at least 1, got {page_size}")
        self._repository = repository
        self._page_size = page_size

    def get_page(self, criteria: ObservationCriteria, number: int) -> ObservationPage:
        """Page ``number`` (1-based) of the observations matching ``criteria``."""
        if number < 1:
            raise ValueError(f"page numbers start at 1, got {number}")

        items = self._repository.find(
            criteria, limit=self._page_size, offset=(number - 1) * self._page_size
        )
        return ObservationPage(
            items=items,
            number=number,
            size=self._page_size,
            total_items=self._repository.count(criteria),
        )

    def get_filter_options(self) -> FilterOptions:
        return FilterOptions(
            countries=self._repository.list_countries(),
            indicators=self._repository.list_indicators(),
            regions=self._repository.list_regions(),
            sexes=tuple(Option(value=sex.value, label=SEX_LABELS[sex]) for sex in Sex),
        )
