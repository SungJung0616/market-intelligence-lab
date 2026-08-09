"""Normalized market-data models shared across repository boundaries."""

from dataclasses import dataclass
from datetime import date, datetime


@dataclass(frozen=True, slots=True)
class Observation:
    date: date
    value: float


@dataclass(frozen=True, slots=True)
class SeriesData:
    source: str
    series_id: str
    collected_at: datetime
    observations: tuple[Observation, ...]

