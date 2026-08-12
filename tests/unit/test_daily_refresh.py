import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from market_intelligence_lab.jobs.run_daily_refresh import RefreshTask, run_daily_refresh


def test_daily_refresh_continues_after_independent_failure(tmp_path) -> None:
    executed: list[str] = []

    def succeed(name: str) -> Path:
        executed.append(name)
        destination = tmp_path / f"{name}.json"
        destination.write_text("valid", encoding="utf-8")
        return destination

    def fail() -> Path:
        executed.append("failed")
        raise RuntimeError("secret provider detail")

    timestamps = iter(
        (
            datetime(2026, 8, 11, 20, 0, tzinfo=timezone.utc),
            datetime(2026, 8, 11, 20, 1, tzinfo=timezone.utc),
        )
    )
    status = run_daily_refresh(
        (
            RefreshTask("first", lambda: succeed("first")),
            RefreshTask("broken", fail),
            RefreshTask("last", lambda: succeed("last")),
        ),
        tmp_path / "processed",
        lambda: next(timestamps),
    )

    assert executed == ["first", "failed", "last"]
    assert status.status == "partial_failure"
    assert status.succeeded == 2
    assert status.failed == 1
    assert status.tasks[1].error_type == "RuntimeError"
    saved = (tmp_path / "processed" / "refresh" / "latest.json").read_text(encoding="utf-8")
    assert "secret provider detail" not in saved


def test_daily_refresh_writes_success_summary(tmp_path) -> None:
    destination = tmp_path / "evidence.json"
    status = run_daily_refresh(
        (RefreshTask("evidence", lambda: destination),),
        tmp_path / "processed",
    )
    payload = json.loads(
        (tmp_path / "processed" / "refresh" / "latest.json").read_text(encoding="utf-8")
    )
    assert status.status == "success"
    assert payload["succeeded"] == 1
    assert payload["failed"] == 0


def test_daily_refresh_rejects_concurrent_run(tmp_path) -> None:
    lock = tmp_path / "processed" / "refresh" / ".lock"
    lock.parent.mkdir(parents=True)
    lock.write_text("running", encoding="utf-8")
    with pytest.raises(RuntimeError, match="already running"):
        run_daily_refresh((), tmp_path / "processed")
