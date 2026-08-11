from datetime import date, datetime, timezone

import pytest

from market_intelligence_lab.analysis.inflation_explanation import explain_inflation
from market_intelligence_lab.collection.models import Observation, SeriesData
from market_intelligence_lab.intelligence.inflation import CONFIGS, calculate_inflation


def _series(series_id: str, monthly_rate: float) -> SeriesData:
    observations = []
    value = 100.0
    year, month = 2020, 1
    for _ in range(80):
        observations.append(Observation(date(year, month, 1), value))
        value *= 1 + monthly_rate
        month += 1
        if month == 13:
            year += 1
            month = 1
    return SeriesData("FRED", series_id, datetime.now(timezone.utc), tuple(observations))


def test_explanation_preserves_score_and_exposes_weighted_contributions() -> None:
    result = calculate_inflation({series_id: _series(series_id, 0.001) for series_id in CONFIGS})
    explanation = explain_inflation(result)
    assert sum(item.weighted_points for item in explanation.indicators) == pytest.approx(
        result.score
    )
    assert {item.weight for item in explanation.indicators} == {0.35, 0.30, 0.20, 0.15}
    assert (
        result.score
        == calculate_inflation(
            {series_id: _series(series_id, 0.001) for series_id in CONFIGS}
        ).score
    )


def test_explanation_reports_imputation_risk_and_confidence() -> None:
    series = {series_id: _series(series_id, 0.001) for series_id in CONFIGS}
    for series_id in ("CPIAUCSL", "CPILFESL"):
        current = series[series_id]
        series[series_id] = SeriesData(
            current.source,
            current.series_id,
            current.collected_at,
            tuple(item for item in current.observations if item.date != date(2025, 10, 1)),
        )
    result = calculate_inflation(series)
    explanation = explain_inflation(result)
    assert explanation.headline
    assert explanation.strongest_evidence.startswith("Strongest relief evidence")
    assert explanation.weakest_evidence.startswith("Weakest relief evidence")
    assert any("not vintage-safe" in risk for risk in explanation.risks)
    assert any("October 2025" in risk for risk in explanation.risks)
    assert explanation.confidence_note.startswith("Moderate confidence")
