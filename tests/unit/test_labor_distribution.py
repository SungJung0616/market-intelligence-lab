from datetime import date, datetime, timedelta, timezone

import pytest

from market_intelligence_lab.collection.models import Observation, SeriesData
from market_intelligence_lab.intelligence.labor_distribution import (
    REQUIRED_SERIES,
    analyze_labor_distributions,
)


def _monthly(series_id: str, start: float, step: float = 1.0) -> SeriesData:
    observations = []
    year, month = 2018, 1
    for index in range(100):
        observations.append(Observation(date(year, month, 1), start + index * step))
        month += 1
        if month == 13:
            year += 1
            month = 1
    return SeriesData("FRED", series_id, datetime.now(timezone.utc), tuple(observations))


def _weekly() -> SeriesData:
    start = date(2018, 1, 6)
    observations = tuple(
        Observation(start + timedelta(weeks=index), 200_000 + index * 100) for index in range(440)
    )
    return SeriesData("FRED", "ICSA", datetime.now(timezone.utc), observations)


def _series() -> dict[str, SeriesData]:
    return {
        "PAYEMS": _monthly("PAYEMS", 140_000, 150),
        "UNRATE": _monthly("UNRATE", 4.0, 0.01),
        "ICSA": _weekly(),
        "JTSJOL": _monthly("JTSJOL", 7_000, 10),
        "JTSJOR": _monthly("JTSJOR", 4.0, 0.01),
        "UNEMPLOY": _monthly("UNEMPLOY", 7_000, 5),
        "CES0500000003": _monthly("CES0500000003", 25.0, 0.1),
    }


def test_analysis_profiles_candidates_without_approving_a_score() -> None:
    report = analyze_labor_distributions(_series())

    profiles = {metric.metric_id: metric for metric in report.metrics}
    assert report.source_series == tuple(sorted(REQUIRED_SERIES))
    assert report.scoring_approved is False
    assert report.vintage_safe is False
    assert profiles["payroll_3m_average"].current == pytest.approx(150)
    assert profiles["payroll_3m_vs_6m"].current == pytest.approx(0)
    assert profiles["jolts_openings_per_unemployed"].current > 1
    assert profiles["jolts_ratio_3m_change"].full_history.count > 90
    assert profiles["claims_13w_change"].full_history.count > 300
    assert profiles["wage_yoy"].recent_5y.count > 50
    assert profiles["wage_momentum_gap"].full_history.count > 80


def test_analysis_requires_every_official_dependency() -> None:
    series = _series()
    del series["UNEMPLOY"]

    with pytest.raises(ValueError, match="UNEMPLOY"):
        analyze_labor_distributions(series)
