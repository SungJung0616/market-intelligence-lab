"""Collect official labor series and publish a descriptive research report."""

import os
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Protocol

from market_intelligence_lab.collection.fred import FredClient
from market_intelligence_lab.collection.models import SeriesData
from market_intelligence_lab.intelligence.labor_distribution import (
    REQUIRED_SERIES,
    analyze_labor_distributions,
)
from market_intelligence_lab.jobs.collect_fred import SUPPORTED_SERIES
from market_intelligence_lab.storage.json_store import save_series
from market_intelligence_lab.storage.labor_research_store import (
    LaborResearchArtifact,
    save_labor_research_artifact,
)


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
        for series_id in sorted(REQUIRED_SERIES)
    }
    report = analyze_labor_distributions(collected)
    timestamp = calculated_at or datetime.now(timezone.utc)
    data_as_of = max(metric.reference_date for metric in report.metrics)
    for series in collected.values():
        save_series(series, raw_root)
    return save_labor_research_artifact(
        LaborResearchArtifact(report, timestamp, data_as_of), processed_root
    )


def main() -> None:
    destination = run_pipeline(FredClient(os.environ.get("FRED_API_KEY", "")))
    print(f"Published labor distribution research to {destination}")


if __name__ == "__main__":
    main()
