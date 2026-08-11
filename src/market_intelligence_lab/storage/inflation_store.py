"""Atomic persistence for validated, processed inflation results."""

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from market_intelligence_lab.intelligence.inflation import IndicatorResult, InflationResult


@dataclass(frozen=True, slots=True)
class InflationArtifact:
    result: InflationResult
    calculated_at: datetime
    data_as_of: str
    completeness: str = "complete"


def save_inflation_artifact(
    artifact: InflationArtifact,
    root: Path = Path("data/processed"),
) -> Path:
    destination = root / "inflation" / f"{artifact.data_as_of}.json"
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
            json.dumps(document, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return destination


def load_inflation_artifact(path: Path) -> InflationArtifact:
    payload: Any = json.loads(path.read_text(encoding="utf-8"))
    try:
        result_payload = payload["result"]
        indicators = tuple(
            IndicatorResult(**{**item, "imputed_dates": tuple(item["imputed_dates"])})
            for item in result_payload["indicators"]
        )
        result = InflationResult(
            score=float(result_payload["score"]),
            condition=str(result_payload["condition"]),
            pressure_label=str(result_payload["pressure_label"]),
            indicators=indicators,
            uses_imputed_data=bool(result_payload["uses_imputed_data"]),
            market_bias=None,
            vintage_safe=bool(result_payload["vintage_safe"]),
            calculation_version=str(result_payload["calculation_version"]),
        )
        completeness = str(payload["completeness"])
        if completeness != "complete":
            raise ValueError("Processed inflation artifact is incomplete")
        return InflationArtifact(
            result=result,
            calculated_at=datetime.fromisoformat(payload["calculated_at"]),
            data_as_of=str(payload["data_as_of"]),
            completeness=completeness,
        )
    except (KeyError, TypeError, ValueError) as exc:
        raise ValueError(f"Invalid inflation artifact: {path}") from exc


def latest_inflation_path(root: Path = Path("data/processed")) -> Path:
    candidates = sorted((root / "inflation").glob("*.json"))
    if not candidates:
        raise FileNotFoundError("No processed inflation result found")
    return candidates[-1]
