"""Deterministic explanations derived from completed Inflation Score results."""

from dataclasses import dataclass

from market_intelligence_lab.intelligence.inflation import CONFIGS, InflationResult


@dataclass(frozen=True, slots=True)
class IndicatorExplanation:
    series_id: str
    label: str
    weight: float
    score: float
    weighted_points: float
    regime: str
    evidence: str


@dataclass(frozen=True, slots=True)
class InflationExplanation:
    headline: str
    summary: str
    indicators: tuple[IndicatorExplanation, ...]
    strongest_evidence: str
    weakest_evidence: str
    conflicts: tuple[str, ...]
    risks: tuple[str, ...]
    confidence_note: str


SUMMARY_BY_CONDITION = {
    "Cooling": (
        "Inflation pressure is easing overall.",
        "The combined evidence is more consistent with cooling than renewed acceleration, "
        "although individual indicators may still disagree.",
    ),
    "Stable": (
        "Inflation pressure is broadly stable.",
        "The evidence does not show a strong move toward either cooling or reacceleration.",
    ),
    "Reaccelerating": (
        "Inflation pressure is rebuilding.",
        "The combined evidence shows renewed price pressure across the measured indicators.",
    ),
    "Mixed": (
        "Inflation signals are mixed.",
        "The indicators disagree, so the combined result should be read with caution.",
    ),
}


def _evidence(label: str, regime: str) -> str:
    descriptions = {
        "Cooling": "shows easing inflation pressure",
        "Stable": "shows broadly stable inflation pressure",
        "Reaccelerating": "shows renewed inflation pressure",
        "Mixed": "contains conflicting short- and medium-term signals",
    }
    return f"{label} {descriptions[regime]}."


def explain_inflation(result: InflationResult) -> InflationExplanation:
    """Explain an existing score without recalculating or changing it."""
    headline, summary = SUMMARY_BY_CONDITION[result.condition]
    indicators = tuple(
        IndicatorExplanation(
            series_id=indicator.series_id,
            label=indicator.label,
            weight=CONFIGS[indicator.series_id].weight,
            score=indicator.score,
            weighted_points=indicator.score * CONFIGS[indicator.series_id].weight,
            regime=indicator.regime,
            evidence=_evidence(indicator.label, indicator.regime),
        )
        for indicator in result.indicators
    )
    strongest = max(indicators, key=lambda item: item.score)
    weakest = min(indicators, key=lambda item: item.score)

    conflicts: list[str] = []
    regimes = {item.regime for item in indicators}
    if len(regimes - {"Stable"}) > 1 or "Mixed" in regimes:
        conflicts.append(
            "The four price indexes do not provide one uniform signal; review CPI and PCE "
            "components separately."
        )
    core = {item.series_id: item.regime for item in indicators}
    if core["CPILFESL"] != core["PCEPILFE"]:
        conflicts.append(f"Core CPI is {core['CPILFESL']}, while Core PCE is {core['PCEPILFE']}.")

    risks = ["Latest FRED values may be revised; this result is not vintage-safe."]
    if result.uses_imputed_data:
        risks.append(
            "October 2025 CPI values are estimated under the approved structural-gap policy."
        )
    risks.append("This inflation reading is not a market-direction or investment signal.")

    return InflationExplanation(
        headline=headline,
        summary=summary,
        indicators=indicators,
        strongest_evidence=(
            f"Strongest relief evidence: {strongest.label} at {strongest.score:.1f}/100."
        ),
        weakest_evidence=(f"Weakest relief evidence: {weakest.label} at {weakest.score:.1f}/100."),
        conflicts=tuple(conflicts),
        risks=tuple(risks),
        confidence_note=(
            "Moderate confidence: all four indicators are present, but revisions and "
            "documented CPI imputation limit certainty."
            if result.uses_imputed_data
            else "Higher confidence: all four indicators are present without imputation."
        ),
    )
