"""Minimal Streamlit previews for collected market evidence."""

from dataclasses import dataclass
from pathlib import Path

import streamlit as st

from market_intelligence_lab.presentation.series import build_figure, summarize
from market_intelligence_lab.storage.json_store import latest_series_path, load_series


@dataclass(frozen=True, slots=True)
class PreviewConfig:
    series_id: str
    title: str
    value_suffix: str
    change_suffix: str
    yaxis_title: str


PREVIEWS = (
    PreviewConfig("DGS10", "10-Year Treasury Rate", "%", "pp", "Percent"),
    PreviewConfig("VIXCLS", "CBOE Volatility Index", "", "pts", "Index level"),
)


def render_preview(config: PreviewConfig) -> None:
    st.subheader(f"{config.title} · {config.series_id}")
    try:
        artifact = latest_series_path(Path("data/raw"), "FRED", config.series_id)
        series = load_series(artifact)
        summary = summarize(series)
    except (FileNotFoundError, ValueError) as exc:
        st.warning(str(exc))
        return

    latest = series.observations[-1]
    col1, col2, col3 = st.columns(3)
    col1.metric(
        "Latest",
        f"{summary.latest:.2f}{config.value_suffix}",
        f"{summary.previous_change:+.2f} {config.change_suffix}",
    )
    col2.metric("Historical mean", f"{summary.historical_mean:.2f}{config.value_suffix}")
    col3.metric("Latest observation", latest.date.isoformat())
    st.plotly_chart(
        build_figure(series, summary.historical_mean, config.yaxis_title),
        use_container_width=True,
        key=config.series_id,
    )
    st.caption(
        f"Source: {series.source} · {len(series.observations):,} observations · "
        f"Collected {series.collected_at.date().isoformat()}"
    )


st.set_page_config(page_title="Market Intelligence Lab", page_icon="📈", layout="wide")
st.title("Market Intelligence Lab")
st.caption("Simple on the surface. Rigorous underneath.")

for preview in PREVIEWS:
    render_preview(preview)
    st.divider()

st.info("Data-quality previews only — not market scores, predictions, or investment signals.")

