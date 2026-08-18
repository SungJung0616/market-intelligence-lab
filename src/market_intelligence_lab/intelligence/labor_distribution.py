"""Descriptive labor-market research transforms; no production scoring."""

from dataclasses import dataclass
from datetime import date
from math import floor

from market_intelligence_lab.collection.models import Observation, SeriesData

VERSION = "labor-distribution-v1"
REQUIRED_SERIES = {
    "PAYEMS",
    "UNRATE",
    "ICSA",
    "JTSJOL",
    "JTSJOR",
    "UNEMPLOY",
    "CES0500000003",
}


@dataclass(frozen=True, slots=True)
class DistributionSummary:
    count: int
    minimum: float
    p05: float
    p25: float
    median: float
    p75: float
    p95: float
    maximum: float


@dataclass(frozen=True, slots=True)
class MetricProfile:
    metric_id: str
    label: str
    reference_date: str
    current: float
    history_start: str
    history_end: str
    full_history: DistributionSummary
    recent_5y: DistributionSummary
    recent_5y_percentile: float
    recent_5y_ex_pandemic: DistributionSummary | None
    pandemic_median: float | None
    pandemic_distortion_note: str | None


@dataclass(frozen=True, slots=True)
class LaborDistributionReport:
    metrics: tuple[MetricProfile, ...]
    source_series: tuple[str, ...]
    scoring_approved: bool = False
    vintage_safe: bool = False
    calculation_version: str = VERSION


def _quantile(sorted_values: list[float], probability: float) -> float:
    position = (len(sorted_values) - 1) * probability
    lower = floor(position)
    upper = min(lower + 1, len(sorted_values) - 1)
    fraction = position - lower
    return sorted_values[lower] + fraction * (sorted_values[upper] - sorted_values[lower])


def _summary(values: list[float]) -> DistributionSummary:
    if not values:
        raise ValueError("Distribution requires at least one value")
    ordered = sorted(values)
    return DistributionSummary(
        len(ordered),
        ordered[0],
        _quantile(ordered, 0.05),
        _quantile(ordered, 0.25),
        _quantile(ordered, 0.50),
        _quantile(ordered, 0.75),
        _quantile(ordered, 0.95),
        ordered[-1],
    )


def _profile(metric_id: str, label: str, values: list[Observation]) -> MetricProfile:
    if len(values) < 24:
        raise ValueError(f"{metric_id} requires at least 24 observations")
    current = values[-1]
    five_year_start = date(current.date.year - 5, current.date.month, current.date.day)
    recent = [item for item in values if item.date >= five_year_start]
    non_pandemic = [
        item for item in recent if not date(2020, 1, 1) <= item.date <= date(2021, 12, 31)
    ]
    pandemic = [
        item.value for item in values if date(2020, 1, 1) <= item.date <= date(2021, 12, 31)
    ]
    below = sum(item.value < current.value for item in recent)
    equal = sum(item.value == current.value for item in recent)
    percentile = (below + 0.5 * equal) / len(recent) * 100
    recent_summary = _summary([item.value for item in recent])
    clean_summary = _summary([item.value for item in non_pandemic]) if non_pandemic else None
    pandemic_median = _summary(pandemic).median if pandemic else None
    note = None
    if pandemic_median is not None and clean_summary is not None:
        baseline = clean_summary.median
        difference = pandemic_median - baseline
        note = (
            "Pandemic observations retained. Pandemic median differs from the recent non-pandemic "
            f"median by {difference:.4g}; no observations were removed from raw data."
        )
    return MetricProfile(
        metric_id,
        label,
        current.date.isoformat(),
        current.value,
        values[0].date.isoformat(),
        current.date.isoformat(),
        _summary([item.value for item in values]),
        recent_summary,
        percentile,
        clean_summary,
        pandemic_median,
        note,
    )


def _rolling_average(values: tuple[Observation, ...], window: int) -> list[Observation]:
    return [
        Observation(
            values[index].date,
            sum(item.value for item in values[index - window + 1 : index + 1]) / window,
        )
        for index in range(window - 1, len(values))
    ]


def _change(values: tuple[Observation, ...], periods: int) -> list[Observation]:
    return [
        Observation(values[index].date, values[index].value - values[index - periods].value)
        for index in range(periods, len(values))
    ]


def _growth(
    values: tuple[Observation, ...], periods: int, annualization: float = 1.0
) -> list[Observation]:
    results = []
    for index in range(periods, len(values)):
        previous = values[index - periods].value
        if previous <= 0:
            raise ValueError("Growth calculations require positive values")
        growth = ((values[index].value / previous) ** annualization - 1) * 100
        results.append(Observation(values[index].date, growth))
    return results


def _ratio(numerator: SeriesData, denominator: SeriesData) -> list[Observation]:
    denominators = {item.date: item.value for item in denominator.observations}
    return [
        Observation(item.date, item.value / denominators[item.date])
        for item in numerator.observations
        if item.date in denominators and denominators[item.date] > 0
    ]


def _aligned_difference(left: list[Observation], right: list[Observation]) -> list[Observation]:
    right_by_date = {item.date: item.value for item in right}
    return [
        Observation(item.date, item.value - right_by_date[item.date])
        for item in left
        if item.date in right_by_date
    ]


def analyze_labor_distributions(series_by_id: dict[str, SeriesData]) -> LaborDistributionReport:
    missing = REQUIRED_SERIES - set(series_by_id)
    if missing:
        raise ValueError(f"Missing labor series: {', '.join(sorted(missing))}")

    payroll = series_by_id["PAYEMS"].observations
    unemployment = series_by_id["UNRATE"].observations
    claims_4w = tuple(_rolling_average(series_by_id["ICSA"].observations, 4))
    wages = series_by_id["CES0500000003"].observations
    unemployment_3m = tuple(_rolling_average(unemployment, 3))
    payroll_changes = tuple(_change(payroll, 1))
    payroll_3m = _rolling_average(payroll_changes, 3)
    payroll_6m = _rolling_average(payroll_changes, 6)
    jolts_ratio = tuple(_ratio(series_by_id["JTSJOL"], series_by_id["UNEMPLOY"]))
    wage_yoy = _growth(wages, 12)
    wage_3m_annualized = _growth(wages, 3, 4.0)
    sahm_gap = [
        Observation(
            unemployment_3m[index].date,
            unemployment_3m[index].value
            - min(item.value for item in unemployment_3m[index - 12 : index]),
        )
        for index in range(12, len(unemployment_3m))
    ]

    candidates = (
        ("payroll_monthly_change", "Payroll monthly change (thousands)", list(payroll_changes)),
        ("payroll_3m_average", "Payroll 3M average monthly change (thousands)", payroll_3m),
        ("payroll_6m_average", "Payroll 6M average monthly change (thousands)", payroll_6m),
        (
            "payroll_3m_vs_6m",
            "Payroll 3M average minus 6M average (thousands)",
            _aligned_difference(payroll_3m, payroll_6m),
        ),
        ("unemployment_rate", "Unemployment rate (%)", list(unemployment)),
        ("unemployment_3m_change", "Unemployment rate 3M change (pp)", _change(unemployment, 3)),
        ("unemployment_6m_change", "Unemployment rate 6M change (pp)", _change(unemployment, 6)),
        ("sahm_gap", "3M unemployment average versus prior 12M low (pp)", sahm_gap),
        ("claims_4w_average", "Initial claims 4W average", list(claims_4w)),
        ("claims_13w_change", "Initial claims 4W average 13W change (%)", _growth(claims_4w, 13)),
        ("jolts_openings_per_unemployed", "Job openings per unemployed worker", list(jolts_ratio)),
        ("jolts_ratio_3m_change", "Job openings per unemployed 3M change", _change(jolts_ratio, 3)),
        (
            "jolts_openings_rate",
            "JOLTS job openings rate (%)",
            list(series_by_id["JTSJOR"].observations),
        ),
        ("wage_yoy", "Average hourly earnings YoY (%)", wage_yoy),
        ("wage_3m_annualized", "Average hourly earnings 3M annualized (%)", wage_3m_annualized),
        (
            "wage_momentum_gap",
            "AHE 3M annualized minus YoY (pp)",
            _aligned_difference(wage_3m_annualized, wage_yoy),
        ),
    )
    return LaborDistributionReport(
        metrics=tuple(
            _profile(metric_id, label, values) for metric_id, label, values in candidates
        ),
        source_series=tuple(sorted(REQUIRED_SERIES)),
    )
