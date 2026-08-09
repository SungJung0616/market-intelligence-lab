"""Deterministic local JSON persistence for normalized series data."""

import json
from datetime import date, datetime
from pathlib import Path
from typing import Any

from market_intelligence_lab.collection.models import Observation, SeriesData


def save_series(data: SeriesData, root: Path = Path("data/raw")) -> Path:
    latest_date = data.observations[-1].date
    destination = root / data.source.lower() / data.series_id.lower() / f"{latest_date}.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(_to_document(data), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return destination


def load_series(path: Path) -> SeriesData:
    payload: Any = json.loads(path.read_text(encoding="utf-8"))
    try:
        return SeriesData(
            source=str(payload["source"]),
            series_id=str(payload["series_id"]),
            collected_at=datetime.fromisoformat(payload["collected_at"]),
            observations=tuple(
                Observation(date=date.fromisoformat(item["date"]), value=float(item["value"]))
                for item in payload["observations"]
            ),
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid series artifact: {path}") from exc


def latest_series_path(root: Path, source: str, series_id: str) -> Path:
    candidates = sorted((root / source.lower() / series_id.lower()).glob("*.json"))
    if not candidates:
        raise FileNotFoundError(f"No saved {source}/{series_id} dataset found")
    return candidates[-1]


def _to_document(data: SeriesData) -> dict[str, object]:
    return {
        "collected_at": data.collected_at.isoformat(),
        "observations": [
            {"date": observation.date.isoformat(), "value": observation.value}
            for observation in data.observations
        ],
        "series_id": data.series_id,
        "source": data.source,
    }

