"""Deterministic explanations derived from completed Labor Intelligence results."""

from dataclasses import dataclass

from market_intelligence_lab.intelligence.labor import LaborResult


@dataclass(frozen=True, slots=True)
class LaborExplanation:
    headline: str
    summary: str
    strongest_evidence: str
    weakest_evidence: str
    conflicts: tuple[str, ...]
    risks: tuple[str, ...]
    confidence_note: str


def explain_labor(result: LaborResult) -> LaborExplanation:
    """Explain an existing score without recalculating or changing it."""
    headline = f"Labor conditions are {result.condition.lower()}."
    summary = (
        f"The combined evidence indicates that labor-market momentum is "
        f"{result.direction.lower()}. "
        "This describes labor health only, not market direction."
    )
    strongest = max(result.components, key=lambda item: item.score)
    weakest = min(result.components, key=lambda item: item.score)
    conflicts = []
    if strongest.score - weakest.score >= 25:
        conflicts.append(
            f"{strongest.label} remains much stronger than {weakest.label}; the headline score "
            "should not hide this divergence."
        )
    if result.wage_pressure.trend == "Cooling" and result.condition in {"Strong", "Healthy"}:
        conflicts.append(
            "Labor health remains positive while wage pressure is cooling; these signals answer "
            "different questions and are intentionally kept separate."
        )
    flag_descriptions = {
        "PAYROLL_CONTRACTION": "The three-month payroll average is contracting.",
        "PAYROLL_DECELERATION": "Payroll momentum is weak and still decelerating.",
        "UNEMPLOYMENT_DETERIORATION_WATCH": "Unemployment deterioration is approaching its warning threshold.",
        "SAHM_THRESHOLD_REACHED": "The Sahm-type threshold has been reached; this is a warning, not a recession declaration.",
        "CLAIMS_DETERIORATION_WATCH": "Weekly claims are rising quickly enough to warrant attention.",
        "CLAIMS_DETERIORATION": "Weekly claims show material early deterioration.",
        "CLAIMS_LEVEL_CONFIRMATION": "The claims level confirms elevated layoff pressure.",
        "LABOR_DEMAND_WEAK": "Job openings are weak relative to unemployed workers.",
        "LABOR_DEMAND_SEVERE": "Job openings show severe demand weakness.",
        "LABOR_DEMAND_OVERHEATING": "Labor demand is unusually strong and may add wage pressure.",
        "NEGATIVE_WAGE_GROWTH": "Wage growth is negative and should not be treated as benign low pressure.",
    }
    risks = [flag_descriptions[flag] for flag in result.risk_flags]
    risks.extend(
        (
            "Latest FRED values may be revised; this result is not vintage-safe.",
            "Labor Health is not a Risk-On/Off, recession-certainty, or investment signal.",
        )
    )
    return LaborExplanation(
        headline,
        summary,
        f"Strongest evidence: {strongest.label} at {strongest.score:.1f}/100.",
        f"Weakest evidence: {weakest.label} at {weakest.score:.1f}/100.",
        tuple(conflicts),
        tuple(risks),
        "Moderate confidence: all required indicators are present, but release lags and revisions "
        "limit direct cross-component timing comparisons.",
    )
