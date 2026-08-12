"""Atomic persistence for secret-safe daily refresh status."""

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True, slots=True)
class RefreshTaskResult:
    name: str
    status: str
    destination: str | None
    error_type: str | None


@dataclass(frozen=True, slots=True)
class DailyRefreshStatus:
    started_at: datetime
    finished_at: datetime
    status: str
    succeeded: int
    failed: int
    tasks: tuple[RefreshTaskResult, ...]


def save_refresh_status(
    status: DailyRefreshStatus,
    root: Path = Path("data/processed"),
) -> Path:
    destination = root / "refresh" / "latest.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".json.tmp")
    try:
        temporary.write_text(
            json.dumps(asdict(status), default=_json_default, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return destination


def _json_default(value: object) -> str:
    if isinstance(value, datetime):
        return value.isoformat()
    raise TypeError(f"Unsupported refresh status value: {type(value).__name__}")
