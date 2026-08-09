from datetime import date, datetime, timezone

import pytest

from market_intelligence_lab.collection.models import Observation, SeriesData
from market_intelligence_lab.presentation.series import build_figure, summarize


def test_summary_and_figure_use_saved_values() -> None:
    data = SeriesData(
        source="FRED",
        series_id="DGS10",
        collected_at=datetime(2026, 8, 8, tzinfo=timezone.utc),
        observations=(Observation(date(2026, 8, 7), 4.0), Observation(date(2026, 8, 8), 4.2)),
    )

    summary = summarize(data)
    figure = build_figure(data, summary.historical_mean, "Percent")

    assert summary.latest == 4.2
    assert summary.previous_change == pytest.approx(0.2)
    assert summary.historical_mean == 4.1
    assert list(figure.data[0].y) == [4.0, 4.2]
    assert figure.data[0].name == "DGS10"
