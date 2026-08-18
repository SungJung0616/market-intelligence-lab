from datetime import datetime, timezone

from market_intelligence_lab.intelligence.labor import (
    LaborComponentResult,
    LaborResult,
    WagePressureResult,
)
from market_intelligence_lab.storage.labor_store import (
    LaborArtifact,
    latest_labor_path,
    load_labor_artifact,
    save_labor_artifact,
)


def test_labor_artifact_round_trip_is_atomic(tmp_path) -> None:
    component = LaborComponentResult(
        "payroll", "Payroll", "2026-07-01", 100, 0, 55, 60, 56.25, 1, 56.25, 50, ()
    )
    wage = WagePressureResult("2026-07-01", 3, 3, 0, 40, "Moderate", "Stable", ())
    result = LaborResult(56.25, "Balanced", "Stable", (component,), wage, ())
    artifact = LaborArtifact(result, datetime(2026, 8, 14, tzinfo=timezone.utc), "2026-07-01")

    destination = save_labor_artifact(artifact, tmp_path)

    assert load_labor_artifact(destination) == artifact
    assert latest_labor_path(tmp_path) == destination
    assert not destination.with_suffix(".json.tmp").exists()
