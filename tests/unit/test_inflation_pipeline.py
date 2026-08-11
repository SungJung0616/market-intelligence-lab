from datetime import date, datetime, timezone

import pytest

from market_intelligence_lab.collection.models import Observation, SeriesData
from market_intelligence_lab.jobs.run_inflation_pipeline import run_pipeline
from market_intelligence_lab.storage.inflation_store import load_inflation_artifact


def _series(series_id: str, monthly_rate: float = 0.001) -> SeriesData:
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


class FakeFredClient:
    def __init__(self, fail_on: str | None = None) -> None:
        self.fail_on = fail_on

    def fetch_series(self, series_id: str, observation_start: date) -> SeriesData:
        del observation_start
        if series_id == self.fail_on:
            raise RuntimeError("collection failed")
        return _series(series_id, 0.001)


def test_pipeline_publishes_complete_result_and_raw_series(tmp_path) -> None:
    raw_root = tmp_path / "raw"
    processed_root = tmp_path / "processed"
    destination = run_pipeline(
        FakeFredClient(),
        raw_root,
        processed_root,
        datetime(2026, 8, 11, tzinfo=timezone.utc),
    )
    artifact = load_inflation_artifact(destination)
    assert artifact.completeness == "complete"
    assert artifact.result.calculation_version == "inflation-v1.1"
    assert len(list(raw_root.glob("fred/*/*.json"))) == 4


def test_pipeline_failure_preserves_last_good_processed_result(tmp_path) -> None:
    processed_root = tmp_path / "processed"
    existing = run_pipeline(FakeFredClient(), tmp_path / "raw", processed_root)
    original = existing.read_text(encoding="utf-8")

    with pytest.raises(RuntimeError, match="collection failed"):
        run_pipeline(FakeFredClient("PCEPI"), tmp_path / "raw", processed_root)

    assert existing.read_text(encoding="utf-8") == original
