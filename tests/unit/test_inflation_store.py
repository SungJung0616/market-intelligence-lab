from datetime import date, datetime, timezone

import pytest

from market_intelligence_lab.intelligence.inflation import calculate_inflation
from market_intelligence_lab.collection.models import Observation, SeriesData
from market_intelligence_lab.storage.inflation_store import (
    InflationArtifact,
    latest_inflation_path,
    load_inflation_artifact,
    save_inflation_artifact,
)


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


def _artifact() -> InflationArtifact:
    result = calculate_inflation(
        {
            series_id: _series(series_id, 0.001)
            for series_id in ("PCEPILFE", "CPILFESL", "PCEPI", "CPIAUCSL")
        }
    )
    return InflationArtifact(
        result=result,
        calculated_at=datetime(2026, 8, 11, tzinfo=timezone.utc),
        data_as_of="2026-08-01",
    )


def test_inflation_artifact_round_trip_is_atomic(tmp_path) -> None:
    artifact = _artifact()
    destination = save_inflation_artifact(artifact, tmp_path)
    assert load_inflation_artifact(destination) == artifact
    assert latest_inflation_path(tmp_path) == destination
    assert not destination.with_suffix(".json.tmp").exists()


def test_invalid_processed_artifact_is_rejected(tmp_path) -> None:
    path = tmp_path / "invalid.json"
    path.write_text('{"completeness": "partial"}', encoding="utf-8")
    with pytest.raises(ValueError, match="Invalid inflation artifact"):
        load_inflation_artifact(path)
