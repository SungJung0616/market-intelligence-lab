"""Minimal Streamlit previews for collected market evidence."""

from dataclasses import dataclass
from pathlib import Path

import streamlit as st

from market_intelligence_lab.intelligence.inflation import (
    CONFIGS,
    InflationResult,
    calculate_inflation,
)
from market_intelligence_lab.presentation.series import build_figure, summarize
from market_intelligence_lab.storage.json_store import latest_series_path, load_series


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
    col1, col2, col3 = st.columns(3)
    col1.metric(
        "Latest",
        _format_value(summary.latest, config),
        f"{summary.previous_change:+.2f} {config.change_suffix}",
    )
    col2.metric("Historical mean", _format_value(summary.historical_mean, config))
    col3.metric("Latest observation", latest.date.isoformat())
    st.plotly_chart(
        build_figure(series, summary.historical_mean, config.yaxis_title),
        use_container_width=True,
        key=f"{config.source}-{config.series_id}",
    )
    st.caption(
        f"{config.note} Source: {series.source} · {len(series.observations):,} observations · "
        f"Collected {series.collected_at.date().isoformat()}"
    )


def render_group(previews: tuple[PreviewConfig, ...]) -> None:
    for index, preview in enumerate(previews):
        render_preview(preview)
        if index < len(previews) - 1:
            st.divider()


def load_inflation_result(root: Path = Path("data/raw")) -> InflationResult:
    series_by_id = {
        series_id: load_series(latest_series_path(root, "FRED", series_id)) for series_id in CONFIGS
    }
    return calculate_inflation(series_by_id)


def render_inflation() -> None:
    st.caption(
        "A deterministic reading of inflation pressure—not a prediction or market signal. "
        "Higher = Lower Inflation Pressure."
    )
    try:
        result = load_inflation_result()
    except (FileNotFoundError, ValueError) as exc:
        st.warning(f"Inflation Score unavailable: {exc}")
        return

    score_col, condition_col, pressure_col = st.columns((2, 1, 1))
    score_col.metric("Inflation Score", f"{result.score:.1f} / 100")
    condition_col.metric("Condition", result.condition)
    pressure_col.metric("Inflation Pressure", result.pressure_label)
    st.progress(result.score / 100)

    rows = [
        {
            "Indicator": indicator.label,
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
        f"Calculation: {result.calculation_version} · Market Bias: Not calculated · "
        "Latest revised FRED data; not vintage-safe."
    )


st.set_page_config(page_title="Market Intelligence Lab", page_icon="📈", layout="wide")
st.title("Market Intelligence Lab")
st.caption("Simple on the surface. Rigorous underneath.")

inflation_tab, equities_tab, macro_tab, cross_asset_tab, bitcoin_tab = st.tabs(
    [
        "Inflation Score",
        "U.S. Market ETFs",
        "Rates, Volatility & Dollar",
        "Cross-Asset Evidence",
        "Bitcoin Evidence",
    ]
)
with inflation_tab:
    render_inflation()

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
