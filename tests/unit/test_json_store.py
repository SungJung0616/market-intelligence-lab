from datetime import date, datetime, timezone
from pathlib import Path

from market_intelligence_lab.collection.models import Observation, SeriesData
from market_intelligence_lab.storage.json_store import load_series, save_series


def test_save_series_creates_deterministic_artifact(tmp_path: Path) -> None:
    root = tmp_path
    series = SeriesData(
        source="FRED",
        series_id="DGS10",
        collected_at=datetime(2026, 8, 8, 12, tzinfo=timezone.utc),
        observations=(
            Observation(date(2026, 8, 7), 4.21),
            Observation(date(2026, 8, 8), 4.19),
        ),
    )

    path = save_series(series, root)

    assert path == root / "fred" / "dgs10" / "2026-08-08.json"
    assert load_series(path) == series
    assert path.read_text(encoding="utf-8").endswith("\n")
