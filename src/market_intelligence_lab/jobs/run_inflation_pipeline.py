"""Collect, validate, calculate, and publish the latest Inflation Score."""

import os
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Protocol

from market_intelligence_lab.collection.fred import FredClient
from market_intelligence_lab.collection.models import SeriesData
from market_intelligence_lab.intelligence.inflation import CONFIGS, calculate_inflation
from market_intelligence_lab.jobs.collect_fred import SUPPORTED_SERIES
from market_intelligence_lab.storage.inflation_store import (
    InflationArtifact,
    save_inflation_artifact,
)
from market_intelligence_lab.storage.json_store import save_series


class FredSeriesClient(Protocol):
    def fetch_series(self, series_id: str, observation_start: date) -> SeriesData: ...


def run_pipeline(
    client: FredSeriesClient,
    raw_root: Path = Path("data/raw"),
    processed_root: Path = Path("data/processed"),
    calculated_at: datetime | None = None,
) -> Path:
    collected = {
        series_id: client.fetch_series(series_id, SUPPORTED_SERIES[series_id])
        for series_id in CONFIGS
    }
    result = calculate_inflation(collected)
    timestamp = calculated_at or datetime.now(timezone.utc)
    data_as_of = max(indicator.reference_date for indicator in result.indicators)
    artifact = InflationArtifact(result=result, calculated_at=timestamp, data_as_of=data_as_of)

    for series in collected.values():
        save_series(series, raw_root)
    return save_inflation_artifact(artifact, processed_root)


def main() -> None:
    api_key = os.environ.get("FRED_API_KEY", "")
    destination = run_pipeline(FredClient(api_key))
    artifact = destination.stem
    print(f"Published Inflation Score for {artifact} to {destination}")


if __name__ == "__main__":
    main()
