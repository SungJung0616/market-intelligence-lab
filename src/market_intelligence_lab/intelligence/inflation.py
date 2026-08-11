"""Deterministic Inflation Score v1 calculations.

Higher scores mean lower inflation pressure. They do not imply Risk-On.
"""

from dataclasses import dataclass, replace
from datetime import date
from math import sqrt
from statistics import median

from market_intelligence_lab.collection.models import Observation, SeriesData

VERSION = "inflation-v1.1"
OFFICIAL_STRUCTURAL_GAPS = {
    "CPIAUCSL": (date(2025, 10, 1),),
    "CPILFESL": (date(2025, 10, 1),),
}


@dataclass(frozen=True, slots=True)
class IndicatorConfig:
    series_id: str
    label: str
    weight: float
    anchors: tuple[tuple[float, float], ...]
    trend_saturation: float


CONFIGS = {
    "PCEPILFE": IndicatorConfig(
        "PCEPILFE",
        "Core PCE",
        0.35,
        ((1.5, 100), (2, 85), (2.5, 70), (3, 50), (4, 20), (5, 0)),
        1.0,
    ),
    "CPILFESL": IndicatorConfig(
        "CPILFESL",
        "Core CPI",
        0.30,
        ((1.8, 100), (2.3, 85), (2.8, 70), (3.3, 50), (4.3, 20), (5.3, 0)),
        1.0,
    ),
    "PCEPI": IndicatorConfig(
        "PCEPI",
        "Headline PCE",
        0.20,
        ((1, 100), (2, 85), (2.75, 65), (3.5, 45), (4.5, 20), (6, 0)),
        1.5,
    ),
    "CPIAUCSL": IndicatorConfig(
        "CPIAUCSL",
        "Headline CPI",
        0.15,
        ((1.3, 100), (2.3, 85), (3.1, 65), (3.8, 45), (5, 20), (7, 0)),
        1.5,
    ),
}


@dataclass(frozen=True, slots=True)
class IndicatorResult:
    series_id: str
    label: str
    reference_date: str
    mom: float
    yoy: float
    annualized_3m: float
    annualized_6m: float
    current_pressure: float
    trend: float
    recent_5y_position: float
    score: float
    regime: str
    robust_z: float | None
    extreme_flag: str
    deflation_flag: bool
    imputed_dates: tuple[str, ...]
    data_quality_note: str | None
    calculation_version: str = VERSION


@dataclass(frozen=True, slots=True)
class InflationResult:
    score: float
    condition: str
    pressure_label: str
    indicators: tuple[IndicatorResult, ...]
    uses_imputed_data: bool
    market_bias: None = None
    vintage_safe: bool = False
    calculation_version: str = VERSION


def _interpolate(value: float, anchors: tuple[tuple[float, float], ...]) -> float:
    if value <= anchors[0][0]:
        return anchors[0][1]
    if value >= anchors[-1][0]:
        return anchors[-1][1]
    for (x1, y1), (x2, y2) in zip(anchors, anchors[1:], strict=True):
        if value <= x2:
            return y1 + (value - x1) * (y2 - y1) / (x2 - x1)
    raise AssertionError("unreachable")


def _delta_score(delta: float, saturation: float) -> float:
    return min(100.0, max(0.0, 50.0 - 50.0 * delta / saturation))


def _regime(short: float, medium: float) -> str:
    def direction(delta: float) -> str:
        if delta < -0.15:
            return "Cooling"
        if delta > 0.15:
            return "Reaccelerating"
        return "Stable"

    directions = {direction(short), direction(medium)}
    if directions == {"Stable"}:
        return "Stable"
    if "Cooling" in directions and "Reaccelerating" not in directions:
        return "Cooling"
    if "Reaccelerating" in directions and "Cooling" not in directions:
        return "Reaccelerating"
    return "Mixed"


def _validate_months(values: tuple[Observation, ...]) -> None:
    if len(values) < 64:
        raise ValueError("Inflation scoring requires at least 64 monthly observations")
    recent = values[-64:]
    for previous, current in zip(recent, recent[1:]):
        previous_month = previous.date.year * 12 + previous.date.month
        current_month = current.date.year * 12 + current.date.month
        if current_month - previous_month != 1:
            raise ValueError("Inflation observations must be contiguous monthly data")
    if any(item.value <= 0 for item in recent):
        raise ValueError("Inflation index values must be positive")


def _apply_structural_gap_policy(series: SeriesData) -> tuple[SeriesData, tuple[str, ...]]:
    """Fill only pre-approved official gaps without mutating the collected artifact."""
    approved = set(OFFICIAL_STRUCTURAL_GAPS.get(series.series_id, ()))
    if not approved:
        return series, ()
    observations = list(series.observations)
    imputed: list[str] = []
    for previous, current in zip(observations, observations[1:]):
        previous_month = previous.date.year * 12 + previous.date.month
        current_month = current.date.year * 12 + current.date.month
        if current_month - previous_month != 2:
            continue
        missing_month_number = previous_month + 1
        missing = date(
            (missing_month_number - 1) // 12,
            (missing_month_number - 1) % 12 + 1,
            1,
        )
        if missing in approved:
            observations.append(Observation(missing, sqrt(previous.value * current.value)))
            imputed.append(missing.isoformat())
    observations.sort(key=lambda item: item.date)
    return replace(series, observations=tuple(observations)), tuple(imputed)


def score_indicator(series: SeriesData) -> IndicatorResult:
    config = CONFIGS.get(series.series_id)
    if config is None:
        raise ValueError(f"Unsupported inflation series: {series.series_id}")
    prepared, imputed_dates = _apply_structural_gap_policy(series)
    observations = prepared.observations
    _validate_months(observations)
    current = observations[-1].value
    mom = (current / observations[-2].value - 1) * 100
    yoy = (current / observations[-13].value - 1) * 100
    annualized_3m = ((current / observations[-4].value) ** 4 - 1) * 100
    annualized_6m = ((current / observations[-7].value) ** 2 - 1) * 100
    pressure = 0.6 * _interpolate(annualized_3m, config.anchors) + 0.4 * _interpolate(
        yoy, config.anchors
    )
    short_delta = annualized_3m - annualized_6m
    medium_delta = annualized_6m - yoy
    trend = 0.6 * _delta_score(short_delta, config.trend_saturation) + 0.4 * _delta_score(
        medium_delta, config.trend_saturation
    )
    prior_3m = [
        ((observations[i].value / observations[i - 3].value) ** 4 - 1) * 100
        for i in range(len(observations) - 61, len(observations) - 1)
    ]
    below = sum(value < annualized_3m for value in prior_3m)
    equal = sum(value == annualized_3m for value in prior_3m)
    position = 100 - (below + 0.5 * equal) / len(prior_3m) * 100
    prior_mom = [
        (observations[i].value / observations[i - 1].value - 1) * 100
        for i in range(len(observations) - 61, len(observations) - 1)
    ]
    center = median(prior_mom)
    mad = median(abs(value - center) for value in prior_mom)
    robust_z = None if mad == 0 else 0.67449 * (mom - center) / mad
    magnitude = 0 if robust_z is None else abs(robust_z)
    extreme = "extreme" if magnitude >= 3.5 else "unusual" if magnitude >= 2.5 else "none"
    score = 0.5 * pressure + 0.3 * trend + 0.2 * position
    return IndicatorResult(
        config.series_id,
        config.label,
        observations[-1].date.isoformat(),
        mom,
        yoy,
        annualized_3m,
        annualized_6m,
        pressure,
        trend,
        position,
        score,
        _regime(short_delta, medium_delta),
        robust_z,
        extreme,
        yoy < 0 or annualized_3m < 0,
        imputed_dates,
        (
            "Official 2025-10 CPI gap estimated with the geometric mean of adjacent indexes."
            if imputed_dates
            else None
        ),
    )


def calculate_inflation(series_by_id: dict[str, SeriesData]) -> InflationResult:
    missing = set(CONFIGS) - set(series_by_id)
    if missing:
        raise ValueError(f"Missing inflation series: {', '.join(sorted(missing))}")
    results = tuple(score_indicator(series_by_id[key]) for key in CONFIGS)
    score = sum(result.score * CONFIGS[result.series_id].weight for result in results)
    core = {result.series_id: result.regime for result in results}
    if {core["PCEPILFE"], core["CPILFESL"]} == {"Cooling", "Reaccelerating"}:
        condition = "Mixed"
    elif score >= 60:
        condition = "Cooling"
    elif score <= 40:
        condition = "Reaccelerating"
    elif 45 <= score <= 55:
        condition = "Stable"
    else:
        condition = "Mixed"
    pressure_label = {
        "Cooling": "Lower",
        "Stable": "Moderate",
        "Mixed": "Mixed",
        "Reaccelerating": "Higher",
    }[condition]
    return InflationResult(
        score,
        condition,
        pressure_label,
        results,
        any(result.imputed_dates for result in results),
    )
