"""Atomic persistence for validated Labor Intelligence results."""

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from market_intelligence_lab.intelligence.labor import (
    LaborComponentResult,
    LaborResult,
    WagePressureResult,
)


@dataclass(frozen=True, slots=True)
class LaborArtifact:
    result: LaborResult
    calculated_at: datetime
    data_as_of: str
    completeness: str = "complete"


def save_labor_artifact(artifact: LaborArtifact, root: Path = Path("data/processed")) -> Path:
    destination = root / "labor" / f"{artifact.data_as_of}.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".json.tmp")
    document = {
        "calculated_at": artifact.calculated_at.isoformat(),
        "completeness": artifact.completeness,
        "data_as_of": artifact.data_as_of,
        "result": asdict(artifact.result),
    }
    try:
        temporary.write_text(
            json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return destination


def load_labor_artifact(path: Path) -> LaborArtifact:
    payload: Any = json.loads(path.read_text(encoding="utf-8"))
    try:
        result_payload = payload["result"]
        components = tuple(
            LaborComponentResult(**{**item, "flags": tuple(item["flags"])})
            for item in result_payload["components"]
        )
        wage_payload = result_payload["wage_pressure"]
        wage = WagePressureResult(**{**wage_payload, "flags": tuple(wage_payload["flags"])})
        result = LaborResult(
            score=float(result_payload["score"]),
            condition=str(result_payload["condition"]),
            direction=str(result_payload["direction"]),
            components=components,
            wage_pressure=wage,
            risk_flags=tuple(result_payload["risk_flags"]),
            market_bias=None,
            vintage_safe=bool(result_payload["vintage_safe"]),
            calculation_version=str(result_payload["calculation_version"]),
        )
        if payload["completeness"] != "complete":
            raise ValueError("Processed labor artifact is incomplete")
        return LaborArtifact(
            result,
            datetime.fromisoformat(payload["calculated_at"]),
            str(payload["data_as_of"]),
            "complete",
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid labor artifact: {path}") from exc


def latest_labor_path(root: Path = Path("data/processed")) -> Path:
    candidates = sorted((root / "labor").glob("*.json"))
    if not candidates:
        raise FileNotFoundError("No processed Labor Intelligence result found")
    return candidates[-1]
