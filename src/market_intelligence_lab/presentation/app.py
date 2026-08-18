"""Minimal Streamlit previews for collected market evidence."""

from dataclasses import dataclass
from pathlib import Path
import subprocess

import streamlit as st

from market_intelligence_lab.analysis.inflation_explanation import explain_inflation
from market_intelligence_lab.analysis.labor_explanation import explain_labor
from market_intelligence_lab.presentation.series import build_figure, summarize
from market_intelligence_lab.storage.inflation_store import (
    InflationArtifact,
    latest_inflation_path,
    load_inflation_artifact,
)
from market_intelligence_lab.storage.json_store import latest_series_path, load_series
from market_intelligence_lab.storage.labor_store import (
    LaborArtifact,
    latest_labor_path,
    load_labor_artifact,
)
from market_intelligence_lab.storage.refresh_store import load_refresh_status


@dataclass(frozen=True, slots=True)
class PreviewConfig:
    source: str
    series_id: str
    title: str
    value_prefix: str
    value_suffix: str
    change_suffix: str
    yaxis_title: str
    note: str


EQUITY_PREVIEWS = (
    PreviewConfig(
        "Tiingo",
        "SPY",
        "S&P 500 Representative ETF",
        "$",
        "",
        "$",
        "Adjusted close",
        "SPY adjusted close; not the S&P 500 index itself.",
    ),
    PreviewConfig(
        "Tiingo",
        "QQQ",
        "Nasdaq-100 Representative ETF",
        "$",
        "",
        "$",
        "Adjusted close",
        "QQQ adjusted close; not the Nasdaq Composite or Nasdaq-100 index itself.",
    ),
    PreviewConfig(
        "Tiingo",
        "DIA",
        "Dow Jones Representative ETF",
        "$",
        "",
        "$",
        "Adjusted close",
        "DIA adjusted close; not the Dow Jones Industrial Average itself.",
    ),
    PreviewConfig(
        "Tiingo",
        "IWM",
        "Russell 2000 Representative ETF",
        "$",
        "",
        "$",
        "Adjusted close",
        "IWM adjusted close; not the Russell 2000 index itself.",
    ),
)

MACRO_PREVIEWS = (
    PreviewConfig(
        "FRED",
        "DGS10",
        "10-Year Treasury Rate",
        "",
        "%",
        "pp",
        "Percent",
        "Daily 10-year Treasury constant maturity rate.",
    ),
    PreviewConfig(
        "FRED",
        "DGS2",
        "2-Year Treasury Rate",
        "",
        "%",
        "pp",
        "Percent",
        "Daily 2-year Treasury constant maturity rate.",
    ),
    PreviewConfig(
        "FRED",
        "VIXCLS",
        "CBOE Volatility Index",
        "",
        "",
        "pts",
        "Index level",
        "Daily VIX close reported through FRED.",
    ),
    PreviewConfig(
        "FRED",
        "DTWEXBGS",
        "Nominal Broad U.S. Dollar Index",
        "",
        "",
        "pts",
        "Index level",
        "Trade-weighted broad U.S. dollar index reported through FRED.",
    ),
)

CROSS_ASSET_PREVIEWS = (
    PreviewConfig(
        "Tiingo",
        "GLD",
        "Gold Representative ETF",
        "$",
        "",
        "$",
        "Adjusted close",
        "GLD adjusted close as observable gold evidence; not the spot gold price.",
    ),
    PreviewConfig(
        "Tiingo",
        "TLT",
        "Long-Term Treasury Representative ETF",
        "$",
        "",
        "$",
        "Adjusted close",
        "TLT adjusted close as observable long-duration Treasury evidence.",
    ),
    PreviewConfig(
        "Tiingo",
        "HYG",
        "High-Yield Credit Representative ETF",
        "$",
        "",
        "$",
        "Adjusted close",
        "HYG adjusted close as observable high-yield credit-risk evidence.",
    ),
    PreviewConfig(
        "Tiingo",
        "LQD",
        "Investment-Grade Credit Representative ETF",
        "$",
        "",
        "$",
        "Adjusted close",
        "LQD adjusted close as observable investment-grade credit evidence.",
    ),
    PreviewConfig(
        "Tiingo",
        "USO",
        "Oil Representative ETF",
        "$",
        "",
        "$",
        "Adjusted close",
        "USO adjusted close as observable oil-market evidence; not the spot oil price.",
    ),
)

BITCOIN_PREVIEWS = (
    PreviewConfig(
        "Coinbase",
        "BTC-USD",
        "Bitcoin · U.S. Dollar",
        "$",
        "",
        "$",
        "UTC daily close",
        "Completed Coinbase BTC-USD UTC daily close from a continuously traded 24×7 market.",
    ),
)


def _format_value(value: float, config: PreviewConfig) -> str:
    return f"{config.value_prefix}{value:.2f}{config.value_suffix}"


def _provider_status(config: PreviewConfig) -> str:
    task_name = {
        "FRED": f"fred:{config.series_id}",
        "Tiingo": f"tiingo:{config.series_id}",
        "Coinbase": f"coinbase:{config.series_id}",
    }[config.source]
    try:
        status = load_refresh_status()
    except (FileNotFoundError, ValueError):
        return "Not checked"
    task = next((item for item in status.tasks if item.name == task_name), None)
    if task is None:
        return "Not checked"
    return "Latest available" if task.status == "success" else "Refresh failed"


def render_preview(config: PreviewConfig) -> None:
    st.subheader(f"{config.title} · {config.series_id}")
    try:
        artifact = latest_series_path(Path("data/raw"), config.source, config.series_id)
        series = load_series(artifact)
        summary = summarize(series)
    except (FileNotFoundError, ValueError) as exc:
        st.warning(str(exc))
        return

    latest = series.observations[-1]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "Latest",
        _format_value(summary.latest, config),
        f"{summary.previous_change:+.2f} {config.change_suffix}",
    )
    col2.metric("Historical mean", _format_value(summary.historical_mean, config))
    col3.metric("Latest observation", latest.date.isoformat())
    col4.metric("Provider status", _provider_status(config))
    st.plotly_chart(
        build_figure(series, summary.historical_mean, config.yaxis_title),
        use_container_width=True,
        key=f"{config.source}-{config.series_id}",
    )
    st.caption(
        f"{config.note} Source: {series.source} · {len(series.observations):,} observations · "
        f"Last checked {series.collected_at.astimezone().isoformat(timespec='minutes')}"
    )


def run_manual_refresh() -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "uv",
            "run",
            "--env-file",
            ".env",
            "python",
            "-m",
            "market_intelligence_lab.jobs.run_daily_refresh",
        ],
        check=False,
        capture_output=True,
        text=True,
    )


def render_refresh_control() -> None:
    status_col, action_col = st.columns((3, 1))
    try:
        status = load_refresh_status()
        status_col.caption(
            f"Last refresh: {status.finished_at.astimezone().isoformat(timespec='minutes')} · "
            f"{status.status} · {status.succeeded} succeeded / {status.failed} failed"
        )
    except (FileNotFoundError, ValueError):
        status_col.caption("No Daily Refresh status is available yet.")
    if action_col.button("Refresh Now", type="primary", use_container_width=True):
        with st.spinner("Refreshing all market evidence..."):
            completed = run_manual_refresh()
        if completed.returncode == 0:
            st.success("Daily Market Refresh completed successfully.")
        else:
            st.error("Daily Market Refresh completed with failures. Previous valid data was kept.")
        st.rerun()


def render_group(previews: tuple[PreviewConfig, ...]) -> None:
    for index, preview in enumerate(previews):
        render_preview(preview)
        if index < len(previews) - 1:
            st.divider()


def load_inflation_result(root: Path = Path("data/processed")) -> InflationArtifact:
    return load_inflation_artifact(latest_inflation_path(root))


def render_inflation() -> None:
    st.caption(
        "A deterministic reading of inflation pressure—not a prediction or market signal. "
        "Higher = Lower Inflation Pressure."
    )

    try:
        artifact = load_inflation_result()
    except (FileNotFoundError, ValueError) as exc:
        st.warning(f"Inflation Score unavailable: {exc}")
        return

    result = artifact.result
    score_col, condition_col, pressure_col = st.columns((2, 1, 1))
    score_col.metric("Inflation Score", f"{result.score:.1f} / 100")
    condition_col.metric("Condition", result.condition)
    pressure_col.metric("Inflation Pressure", result.pressure_label)
    st.progress(result.score / 100)

    explanation = explain_inflation(result)
    st.subheader("Why this score?")
    st.markdown(f"**{explanation.headline}** {explanation.summary}")
    evidence_col, caution_col = st.columns(2)
    evidence_col.success(explanation.strongest_evidence)
    caution_col.info(explanation.weakest_evidence)

    rows = [
        {
            "Indicator": indicator.label,
            "Weight": f"{next(item.weight for item in explanation.indicators if item.series_id == indicator.series_id):.0%}",
            "Contribution": round(
                next(
                    item.weighted_points
                    for item in explanation.indicators
                    if item.series_id == indicator.series_id
                ),
                1,
            ),
            "Score": round(indicator.score, 1),
            "Current Pressure": round(indicator.current_pressure, 1),
            "Trend": round(indicator.trend, 1),
            "Recent 5Y Position": round(indicator.recent_5y_position, 1),
            "Condition": indicator.regime,
            "Reference Month": indicator.reference_date[:7],
        }
        for indicator in result.indicators
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)

    if explanation.conflicts:
        st.warning("Conflicting signals\n\n" + "\n\n".join(explanation.conflicts))

    st.caption(explanation.confidence_note)
    with st.expander("Risks and limitations"):
        for risk in explanation.risks:
            st.markdown(f"- {risk}")

    if result.uses_imputed_data:
        dates = sorted(
            {date for indicator in result.indicators for date in indicator.imputed_dates}
        )
        st.warning(
            "Estimated official structural gap: "
            f"{', '.join(dates)} CPI values use the geometric mean of adjacent months. "
            "Raw FRED data remains unchanged."
        )
    st.caption(
        f"Data as of: {artifact.data_as_of[:7]} · Updated: "
        f"{artifact.calculated_at.isoformat(timespec='minutes')} · "
        f"Completeness: {artifact.completeness} · Calculation: "
        f"{result.calculation_version} · Market Bias: Not calculated · "
        "Latest revised FRED data; not vintage-safe."
    )


def load_labor_result(root: Path = Path("data/processed")) -> LaborArtifact:
    return load_labor_artifact(latest_labor_path(root))


def render_labor() -> None:
    st.caption(
        "A deterministic reading of U.S. labor-market health—not a market signal. "
        "Higher = healthier and more resilient labor conditions."
    )
    try:
        artifact = load_labor_result()
    except (FileNotFoundError, ValueError) as exc:
        st.warning(f"Labor Intelligence unavailable: {exc}")
        return

    result = artifact.result
    score_col, condition_col, direction_col, wage_col = st.columns((2, 1, 1, 1))
    score_col.metric("Labor Health", f"{result.score:.1f} / 100")
    condition_col.metric("Condition", result.condition)
    direction_col.metric("Direction", result.direction)
    wage_col.metric(
        "Wage Pressure",
        f"{result.wage_pressure.score:.1f} / 100",
        result.wage_pressure.trend,
    )
    st.progress(result.score / 100)

    explanation = explain_labor(result)
    st.subheader("Why this score?")
    st.markdown(f"**{explanation.headline}** {explanation.summary}")
    evidence_col, caution_col = st.columns(2)
    evidence_col.success(explanation.strongest_evidence)
    caution_col.info(explanation.weakest_evidence)

    rows = [
        {
            "Component": component.label,
            "Weight": f"{component.weight:.0%}",
            "Contribution": round(component.weighted_points, 1),
            "Score": round(component.score, 1),
            "Level Score": round(component.level_score, 1),
            "Trend Score": round(component.trend_score, 1),
            "Recent 5Y Percentile": round(component.recent_5y_percentile, 1),
            "Reference Period": component.reference_date,
            "Flags": ", ".join(component.flags) or "None",
        }
        for component in result.components
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)

    wage = result.wage_pressure
    st.subheader("Wage Pressure · Separate Signal")
    wage_col1, wage_col2, wage_col3, wage_col4 = st.columns(4)
    wage_col1.metric("AHE YoY", f"{wage.yoy:.2f}%")
    wage_col2.metric("AHE 3M Annualized", f"{wage.annualized_3m:.2f}%")
    wage_col3.metric("Momentum Gap", f"{wage.momentum_gap:+.2f} pp")
    wage_col4.metric("Pressure", wage.pressure_label)

    if explanation.conflicts:
        st.warning("Conflicting signals\n\n" + "\n\n".join(explanation.conflicts))
    st.caption(explanation.confidence_note)
    with st.expander("Risks and limitations"):
        for risk in explanation.risks:
            st.markdown(f"- {risk}")
    st.caption(
        f"Data as of: {artifact.data_as_of} · Updated: "
        f"{artifact.calculated_at.isoformat(timespec='minutes')} · "
        f"Completeness: {artifact.completeness} · Calculation: "
        f"{result.calculation_version} · Market Bias: Not calculated · "
        "Latest revised FRED data; not vintage-safe."
    )


st.set_page_config(page_title="Market Intelligence Lab", page_icon="📈", layout="wide")
st.title("Market Intelligence Lab")
st.caption("Simple on the surface. Rigorous underneath.")
render_refresh_control()

inflation_tab, labor_tab, equities_tab, macro_tab, cross_asset_tab, bitcoin_tab = st.tabs(
    [
        "Inflation Score",
        "Labor Intelligence",
        "U.S. Market ETFs",
        "Rates, Volatility & Dollar",
        "Cross-Asset Evidence",
        "Bitcoin Evidence",
    ]
)
with inflation_tab:
    render_inflation()

with labor_tab:
    render_labor()

with equities_tab:
    st.caption(
        "Liquid representative ETFs are used as observable market evidence—not as index substitutes or investment recommendations."
    )
    render_group(EQUITY_PREVIEWS)

with macro_tab:
    st.caption("Macro and risk evidence from official FRED series.")
    render_group(MACRO_PREVIEWS)

with cross_asset_tab:
    st.caption(
        "Representative ETFs provide observable gold, oil, duration, and credit evidence—"
        "not spot prices, scores, or investment recommendations."
    )
    render_group(CROSS_ASSET_PREVIEWS)

with bitcoin_tab:
    st.caption(
        "Bitcoin trades continuously. This view uses only completed UTC daily candles and is "
        "kept separate from exchange-traded market sessions."
    )
    render_group(BITCOIN_PREVIEWS)

st.info("Data-quality previews only — not market scores, predictions, or investment signals.")
