"""Deterministic Labor Health Score v1 and separate Wage Pressure calculations."""

from dataclasses import dataclass

from market_intelligence_lab.intelligence.labor_distribution import (
    LaborDistributionReport,
    MetricProfile,
)

VERSION = "labor-v1.0"

PAYROLL_LEVEL_ANCHORS = ((-100, 0), (0, 20), (50, 40), (100, 55), (175, 75), (250, 90), (350, 100))
PAYROLL_TREND_ANCHORS = ((-100, 0), (-50, 25), (-25, 40), (0, 60), (25, 75), (50, 90), (100, 100))
UNEMPLOYMENT_LEVEL_ANCHORS = (
    (3.0, 100),
    (3.5, 95),
    (4.0, 85),
    (4.5, 70),
    (5.0, 50),
    (6.0, 25),
    (8.0, 0),
)
SAHM_GAP_ANCHORS = ((0.0, 100), (0.1, 85), (0.2, 70), (0.3, 50), (0.4, 25), (0.5, 0))
CLAIMS_LEVEL_ANCHORS = (
    (175_000, 100),
    (200_000, 90),
    (225_000, 75),
    (250_000, 55),
    (300_000, 25),
    (400_000, 0),
)
CLAIMS_TREND_ANCHORS = ((-15, 100), (-5, 85), (0, 65), (5, 45), (10, 25), (15, 10), (25, 0))
JOLTS_LEVEL_ANCHORS = ((0.4, 0), (0.6, 25), (0.8, 50), (1.0, 70), (1.2, 85), (1.5, 95), (2.0, 100))
JOLTS_TREND_ANCHORS = (
    (-0.3, 0),
    (-0.15, 25),
    (-0.05, 45),
    (0.0, 60),
    (0.05, 75),
    (0.15, 95),
    (0.3, 100),
)
WAGE_PRESSURE_ANCHORS = (
    (2.0, 10),
    (2.5, 25),
    (3.0, 40),
    (3.5, 55),
    (4.0, 70),
    (5.0, 90),
    (6.0, 100),
)


@dataclass(frozen=True, slots=True)
class LaborComponentResult:
    component_id: str
    label: str
    reference_date: str
    level_value: float
    trend_value: float
    level_score: float
    trend_score: float
    score: float
    weight: float
    weighted_points: float
    recent_5y_percentile: float
    flags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WagePressureResult:
    reference_date: str
    yoy: float
    annualized_3m: float
    momentum_gap: float
    score: float
    pressure_label: str
    trend: str
    flags: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class LaborResult:
    score: float
    condition: str
    direction: str
    components: tuple[LaborComponentResult, ...]
    wage_pressure: WagePressureResult
    risk_flags: tuple[str, ...]
    market_bias: None = None
    vintage_safe: bool = False
    calculation_version: str = VERSION


def _interpolate(value: float, anchors: tuple[tuple[float, float], ...]) -> float:
    if value <= anchors[0][0]:
        return float(anchors[0][1])
    if value >= anchors[-1][0]:
        return float(anchors[-1][1])
    for (x1, y1), (x2, y2) in zip(anchors, anchors[1:], strict=True):
        if value <= x2:
            return y1 + (value - x1) * (y2 - y1) / (x2 - x1)
    raise AssertionError("unreachable")


def _metrics(report: LaborDistributionReport) -> dict[str, MetricProfile]:
    return {metric.metric_id: metric for metric in report.metrics}


def _component(
    component_id: str,
    label: str,
    level: MetricProfile,
    trend: MetricProfile,
    level_anchors: tuple[tuple[float, float], ...],
    trend_anchors: tuple[tuple[float, float], ...],
    level_weight: float,
    top_weight: float,
    flags: tuple[str, ...],
) -> LaborComponentResult:
    level_score = _interpolate(level.current, level_anchors)
    trend_score = _interpolate(trend.current, trend_anchors)
    score = level_weight * level_score + (1 - level_weight) * trend_score
    return LaborComponentResult(
        component_id,
        label,
        max(level.reference_date, trend.reference_date),
        level.current,
        trend.current,
        level_score,
        trend_score,
        score,
        top_weight,
        score * top_weight,
        level.recent_5y_percentile,
        flags,
    )


def calculate_labor(report: LaborDistributionReport) -> LaborResult:
    """Calculate the approved score from a complete distribution report."""
    if report.scoring_approved:
        raise ValueError("Research input must remain independent from production scoring")
    metrics = _metrics(report)
    required = {
        "payroll_3m_average",
        "payroll_3m_vs_6m",
        "unemployment_rate",
        "sahm_gap",
        "claims_4w_average",
        "claims_13w_change",
        "jolts_openings_per_unemployed",
        "jolts_ratio_3m_change",
        "wage_yoy",
        "wage_3m_annualized",
        "wage_momentum_gap",
    }
    missing = required - set(metrics)
    if missing:
        raise ValueError(f"Missing labor metrics: {', '.join(sorted(missing))}")

    payroll_level = metrics["payroll_3m_average"]
    payroll_trend = metrics["payroll_3m_vs_6m"]
    payroll_flags = []
    if payroll_level.current < 0:
        payroll_flags.append("PAYROLL_CONTRACTION")
    if payroll_level.current < 50 and payroll_trend.current < -25:
        payroll_flags.append("PAYROLL_DECELERATION")

    unemployment_level = metrics["unemployment_rate"]
    sahm = metrics["sahm_gap"]
    unemployment_flags = []
    if sahm.current >= 0.5:
        unemployment_flags.append("SAHM_THRESHOLD_REACHED")
    elif sahm.current >= 0.3:
        unemployment_flags.append("UNEMPLOYMENT_DETERIORATION_WATCH")

    claims_level = metrics["claims_4w_average"]
    claims_trend = metrics["claims_13w_change"]
    claims_flags = []
    if claims_trend.current >= 15:
        claims_flags.append("CLAIMS_DETERIORATION")
    elif claims_trend.current >= 10:
        claims_flags.append("CLAIMS_DETERIORATION_WATCH")
    if claims_level.current >= 250_000:
        claims_flags.append("CLAIMS_LEVEL_CONFIRMATION")

    jolts_level = metrics["jolts_openings_per_unemployed"]
    jolts_trend = metrics["jolts_ratio_3m_change"]
    jolts_flags = []
    if jolts_level.current < 0.6:
        jolts_flags.append("LABOR_DEMAND_SEVERE")
    elif jolts_level.current < 0.8:
        jolts_flags.append("LABOR_DEMAND_WEAK")
    if jolts_level.current >= 1.5:
        jolts_flags.append("LABOR_DEMAND_OVERHEATING")

    components = (
        _component(
            "payroll",
            "Payroll Momentum",
            payroll_level,
            payroll_trend,
            PAYROLL_LEVEL_ANCHORS,
            PAYROLL_TREND_ANCHORS,
            0.75,
            0.30,
            tuple(payroll_flags),
        ),
        _component(
            "unemployment",
            "Unemployment Health",
            unemployment_level,
            sahm,
            UNEMPLOYMENT_LEVEL_ANCHORS,
            SAHM_GAP_ANCHORS,
            0.55,
            0.30,
            tuple(unemployment_flags),
        ),
        _component(
            "claims",
            "Initial Claims",
            claims_level,
            claims_trend,
            CLAIMS_LEVEL_ANCHORS,
            CLAIMS_TREND_ANCHORS,
            0.50,
            0.25,
            tuple(claims_flags),
        ),
        _component(
            "jolts",
            "JOLTS Demand",
            jolts_level,
            jolts_trend,
            JOLTS_LEVEL_ANCHORS,
            JOLTS_TREND_ANCHORS,
            0.75,
            0.15,
            tuple(jolts_flags),
        ),
    )
    score = sum(component.weighted_points for component in components)
    condition = (
        "Strong"
        if score >= 80
        else "Healthy"
        if score >= 65
        else "Balanced"
        if score >= 50
        else "Weakening"
        if score >= 35
        else "Fragile"
    )
    average_trend = sum(component.trend_score * component.weight for component in components)
    direction = (
        "Improving" if average_trend >= 65 else "Stable" if average_trend >= 45 else "Deteriorating"
    )

    wage_yoy = metrics["wage_yoy"]
    wage_3m = metrics["wage_3m_annualized"]
    wage_gap = metrics["wage_momentum_gap"]
    wage_score = 0.70 * _interpolate(wage_yoy.current, WAGE_PRESSURE_ANCHORS) + 0.30 * _interpolate(
        wage_3m.current, WAGE_PRESSURE_ANCHORS
    )
    wage_label = "High" if wage_score >= 70 else "Moderate" if wage_score >= 40 else "Low"
    wage_trend = (
        "Cooling"
        if wage_gap.current < -0.3
        else "Reaccelerating"
        if wage_gap.current > 0.3
        else "Stable"
    )
    wage_flags = ("NEGATIVE_WAGE_GROWTH",) if wage_yoy.current < 0 or wage_3m.current < 0 else ()
    wage = WagePressureResult(
        wage_yoy.reference_date,
        wage_yoy.current,
        wage_3m.current,
        wage_gap.current,
        wage_score,
        wage_label,
        wage_trend,
        wage_flags,
    )
    risks = tuple(flag for component in components for flag in component.flags) + wage.flags
    return LaborResult(score, condition, direction, components, wage, risks)
