import pytest

from market_intelligence_lab.intelligence.labor import calculate_labor
from market_intelligence_lab.intelligence.labor_distribution import (
    DistributionSummary,
    LaborDistributionReport,
    MetricProfile,
)


def _metric(metric_id: str, current: float) -> MetricProfile:
    summary = DistributionSummary(60, current, current, current, current, current, current, current)
    return MetricProfile(
        metric_id,
        metric_id,
        "2026-07-01",
        current,
        "2021-07-01",
        "2026-07-01",
        summary,
        summary,
        50.0,
        summary,
        None,
        None,
    )


def _report(overrides: dict[str, float] | None = None) -> LaborDistributionReport:
    values = {
        "payroll_3m_average": 150.0,
        "payroll_3m_vs_6m": 0.0,
        "unemployment_rate": 4.5,
        "sahm_gap": 0.3,
        "claims_4w_average": 225_000.0,
        "claims_13w_change": 15.0,
        "jolts_openings_per_unemployed": 1.0,
        "jolts_ratio_3m_change": 0.0,
        "wage_yoy": 3.5,
        "wage_3m_annualized": 3.0,
        "wage_momentum_gap": -0.5,
    }
    values.update(overrides or {})
    return LaborDistributionReport(
        tuple(_metric(metric_id, value) for metric_id, value in values.items()), ()
    )


def test_approved_scenarios_use_continuous_curves_and_separate_wages() -> None:
    result = calculate_labor(_report())
    components = {component.component_id: component for component in result.components}

    assert components["payroll"].score == pytest.approx(66.25)
    assert components["unemployment"].score == pytest.approx(61.0)
    assert components["claims"].score == pytest.approx(42.5)
    assert components["jolts"].score == pytest.approx(67.5)
    assert result.score == pytest.approx(
        sum(component.weighted_points for component in result.components)
    )
    assert result.wage_pressure.score not in {component.score for component in result.components}
    assert result.market_bias is None
    assert result.vintage_safe is False


def test_flags_surface_deterioration_and_overheating_without_overriding_scores() -> None:
    result = calculate_labor(
        _report(
            {
                "payroll_3m_average": -10,
                "sahm_gap": 0.5,
                "claims_13w_change": 16,
                "claims_4w_average": 260_000,
                "jolts_openings_per_unemployed": 1.6,
            }
        )
    )

    assert "PAYROLL_CONTRACTION" in result.risk_flags
    assert "SAHM_THRESHOLD_REACHED" in result.risk_flags
    assert "CLAIMS_DETERIORATION" in result.risk_flags
    assert "CLAIMS_LEVEL_CONFIRMATION" in result.risk_flags
    assert "LABOR_DEMAND_OVERHEATING" in result.risk_flags
    jolts = next(item for item in result.components if item.component_id == "jolts")
    assert jolts.score > 80
