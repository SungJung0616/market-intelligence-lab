from datetime import date, datetime, timezone

import pytest

from market_intelligence_lab.collection.models import Observation, SeriesData
from market_intelligence_lab.intelligence.inflation import calculate_inflation, score_indicator


def _series(series_id: str, monthly_rate: float = 0.002) -> SeriesData:
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


def test_score_indicator_exposes_three_weighted_components() -> None:
    result = score_indicator(_series("PCEPILFE"))
    assert result.score == pytest.approx(
        0.5 * result.current_pressure + 0.3 * result.trend + 0.2 * result.recent_5y_position
    )
    assert result.regime == "Stable"
    assert result.calculation_version == "inflation-v1"


def test_score_indicator_requires_64_contiguous_months() -> None:
    series = _series("CPIAUCSL")
    with pytest.raises(ValueError, match="64 monthly"):
        score_indicator(
            SeriesData(
                series.source, series.series_id, series.collected_at, series.observations[-63:]
            )
        )
    broken = series.observations[:50] + series.observations[51:]
    with pytest.raises(ValueError, match="contiguous"):
        score_indicator(SeriesData(series.source, series.series_id, series.collected_at, broken))


def test_combined_score_requires_all_four_series() -> None:
    with pytest.raises(ValueError, match="Missing inflation series"):
        calculate_inflation({"PCEPILFE": _series("PCEPILFE")})


def test_combined_score_uses_relief_direction() -> None:
    result = calculate_inflation(
        {
            series_id: _series(series_id, 0.001)
            for series_id in ("PCEPILFE", "CPILFESL", "PCEPI", "CPIAUCSL")
        }
    )
    assert result.score >= 60
    assert result.condition == "Cooling"
    assert result.pressure_label == "Lower"
    assert result.market_bias is None
    assert result.vintage_safe is False
