"""SQLAlchemy models: the five tables of db/schema.sql as Python classes."""
from datetime import datetime
from decimal import Decimal
from enum import StrEnum

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    false,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class Sex(StrEnum):
    """Sex dimension of an observation (WHO GHO codes without the SEX_ prefix)."""

    BOTH = "BTSX"
    MALE = "MLE"
    FEMALE = "FMLE"


class ResidenceArea(StrEnum):
    """Area of residence (WHO GHO codes without the RESIDENCEAREATYPE_ prefix)."""

    TOTAL = "TOTL"
    URBAN = "URB"
    RURAL = "RUR"


class Source(Base):
    """Where the data comes from (WHO GHO, World Bank, Our World in Data)."""
    __tablename__ = "source"

    source_id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    url: Mapped[str | None] = mapped_column(Text)


class Country(Base):
    """Countries only (no aggregates such as "World"), keyed by ISO3."""
    __tablename__ = "country"

    iso3: Mapped[str] = mapped_column(String(3), primary_key=True)
    iso2: Mapped[str | None] = mapped_column(String(2))
    name: Mapped[str] = mapped_column(String(100))
    region: Mapped[str | None] = mapped_column(String(100))
    income_group: Mapped[str | None] = mapped_column(String(50))


class Indicator(Base):
    """What is measured, with its unit and source."""
    __tablename__ = "indicator"

    indicator_id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(50), unique=True)
    name: Mapped[str] = mapped_column(String(255))
    unit: Mapped[str | None] = mapped_column(String(50))
    source_id: Mapped[int] = mapped_column(ForeignKey("source.source_id"))

    source: Mapped[Source] = relationship()


class Observation(Base):
    """Fact table: one value per country, indicator, year, sex and area of residence."""
    __tablename__ = "observation"
    __table_args__ = (
        UniqueConstraint("country_iso3", "indicator_id", "year", "sex", "residence_area",
                         name="uq_observation"),
        Index("ix_observation_indicator_year", "indicator_id", "year"),
    )

    observation_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    country_iso3: Mapped[str] = mapped_column(ForeignKey("country.iso3"))
    indicator_id: Mapped[int] = mapped_column(ForeignKey("indicator.indicator_id"))
    year: Mapped[int] = mapped_column(SmallInteger)
    sex: Mapped[str] = mapped_column(String(10), server_default=Sex.BOTH.value)
    # Topic changes (Task 1.8): urban/rural split of PM2.5 and WHO uncertainty intervals
    residence_area: Mapped[str] = mapped_column(String(10),
                                                server_default=ResidenceArea.TOTAL.value)
    value: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    value_low: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    value_high: Mapped[Decimal | None] = mapped_column(Numeric(18, 4))
    # Lab 2, Task 2.2: IQR outlier flag (outliers are flagged, not dropped).
    # Added by the Alembic migration alembic/versions/0002_observation_is_outlier.py.
    is_outlier: Mapped[bool] = mapped_column(Boolean, server_default=false())
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                  server_default=func.now())

    country: Mapped[Country] = relationship()
    indicator: Mapped[Indicator] = relationship()


class ImportLog(Base):
    """Audit trail of every import, for reproducibility."""
    __tablename__ = "import_log"

    import_id: Mapped[int] = mapped_column(primary_key=True)
    source_name: Mapped[str] = mapped_column(String(100))
    indicator_code: Mapped[str] = mapped_column(String(50))
    url: Mapped[str] = mapped_column(Text)
    rows_loaded: Mapped[int]
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True),
                                                  server_default=func.now())
