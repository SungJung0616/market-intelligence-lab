"""Atomic persistence for labor distribution research reports."""

import json
import os
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from market_intelligence_lab.intelligence.labor_distribution import LaborDistributionReport


@dataclass(frozen=True, slots=True)
class LaborResearchArtifact:
    report: LaborDistributionReport
    calculated_at: datetime
    data_as_of: str
    completeness: str = "complete"


def save_labor_research_artifact(
    artifact: LaborResearchArtifact,
    root: Path = Path("data/processed"),
) -> Path:
    destination = root / "labor_research" / f"{artifact.data_as_of}.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".json.tmp")
    document = {
        "calculated_at": artifact.calculated_at.isoformat(),
        "completeness": artifact.completeness,
        "data_as_of": artifact.data_as_of,
        "report": asdict(artifact.report),
    }
    try:
        temporary.write_text(
            json.dumps(document, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        os.replace(temporary, destination)
    finally:
        temporary.unlink(missing_ok=True)
    return destination
