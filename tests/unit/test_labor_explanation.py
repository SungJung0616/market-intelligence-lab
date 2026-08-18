from market_intelligence_lab.analysis.labor_explanation import explain_labor
from market_intelligence_lab.intelligence.labor import (
    LaborComponentResult,
    LaborResult,
    WagePressureResult,
)


def test_explanation_consumes_completed_result_without_recalculating() -> None:
    components = (
        LaborComponentResult(
            "payroll", "Payroll Momentum", "2026-07-01", 20, -24, 28, 41, 31, 0.30, 9.3, 10.7, ()
        ),
        LaborComponentResult(
            "unemployment",
            "Unemployment Health",
            "2026-07-01",
            4.1,
            0,
            82,
            100,
            90,
            0.30,
            27,
            57.5,
            (),
        ),
        LaborComponentResult(
            "claims", "Initial Claims", "2026-08-01", 198750, -2, 90, 73, 82, 0.25, 20.5, 1, ()
        ),
        LaborComponentResult(
            "jolts", "JOLTS Demand", "2026-06-01", 1.04, 0.09, 73, 82, 75, 0.15, 11.25, 27.5, ()
        ),
    )
    wage = WagePressureResult("2026-07-01", 3.15, 2.26, -0.89, 36, "Low", "Cooling", ())
    result = LaborResult(68.05, "Healthy", "Stable", components, wage, ())

    explanation = explain_labor(result)

    assert explanation.strongest_evidence.startswith("Strongest evidence: Unemployment")
    assert explanation.weakest_evidence.startswith("Weakest evidence: Payroll")
    assert any("divergence" in conflict for conflict in explanation.conflicts)
    assert any("not vintage-safe" in risk for risk in explanation.risks)
    assert result.score == 68.05
