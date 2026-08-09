"""Minimal Streamlit previews for collected market evidence."""

from dataclasses import dataclass
from pathlib import Path

import streamlit as st

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
        "Tiingo", "SPY", "S&P 500 Representative ETF", "$", "", "$", "Adjusted close", "SPY adjusted close; not the S&P 500 index itself.",
    ),
    PreviewConfig(
        "Tiingo", "QQQ", "Nasdaq-100 Representative ETF", "$", "", "$", "Adjusted close", "QQQ adjusted close; not the Nasdaq Composite or Nasdaq-100 index itself.",
    ),
    PreviewConfig(
        "Tiingo", "DIA", "Dow Jones Representative ETF", "$", "", "$", "Adjusted close", "DIA adjusted close; not the Dow Jones Industrial Average itself.",
    ),
    PreviewConfig(
        "Tiingo", "IWM", "Russell 2000 Representative ETF", "$", "", "$", "Adjusted close", "IWM adjusted close; not the Russell 2000 index itself.",
    ),
)

MACRO_PREVIEWS = (
    PreviewConfig("FRED", "DGS10", "10-Year Treasury Rate", "", "%", "pp", "Percent", "Daily 10-year Treasury constant maturity rate."),
    PreviewConfig("FRED", "DGS2", "2-Year Treasury Rate", "", "%", "pp", "Percent", "Daily 2-year Treasury constant maturity rate."),
    PreviewConfig("FRED", "VIXCLS", "CBOE Volatility Index", "", "", "pts", "Index level", "Daily VIX close reported through FRED."),
    PreviewConfig("FRED", "DTWEXBGS", "Nominal Broad U.S. Dollar Index", "", "", "pts", "Index level", "Trade-weighted broad U.S. dollar index reported through FRED."),
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


st.set_page_config(page_title="Market Intelligence Lab", page_icon="📈", layout="wide")
st.title("Market Intelligence Lab")
st.caption("Simple on the surface. Rigorous underneath.")

equities_tab, macro_tab = st.tabs(["U.S. Market ETFs", "Rates, Volatility & Dollar"])
with equities_tab:
    st.caption("Liquid representative ETFs are used as observable market evidence—not as index substitutes or investment recommendations.")
    render_group(EQUITY_PREVIEWS)

with macro_tab:
    st.caption("Macro and risk evidence from official FRED series.")
    render_group(MACRO_PREVIEWS)

st.info("Data-quality previews only — not market scores, predictions, or investment signals.")
