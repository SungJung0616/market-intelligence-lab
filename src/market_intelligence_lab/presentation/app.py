"""Minimal Streamlit preview for the first collected market dataset."""

from pathlib import Path

import streamlit as st

from market_intelligence_lab.presentation.dgs10 import build_figure, summarize
from market_intelligence_lab.storage.json_store import latest_series_path, load_series

st.set_page_config(page_title="Market Intelligence Lab", page_icon="📈", layout="wide")
st.title("Market Intelligence Lab")
st.caption("Simple on the surface. Rigorous underneath.")
st.subheader("10-Year Treasury Rate · DGS10")

try:
    artifact = latest_series_path(Path("data/raw"), "FRED", "DGS10")
    series = load_series(artifact)
    summary = summarize(series)
except (FileNotFoundError, ValueError) as exc:
    st.error(str(exc))
    st.stop()

latest = series.observations[-1]
col1, col2, col3 = st.columns(3)
col1.metric("Latest", f"{summary.latest:.2f}%", f"{summary.previous_change:+.2f} pp")
col2.metric("Historical mean", f"{summary.historical_mean:.2f}%")
col3.metric("Latest observation", latest.date.isoformat())

st.plotly_chart(build_figure(series, summary.historical_mean), use_container_width=True)
st.caption(
    f"Source: {series.source} · {len(series.observations):,} observations · "
    f"Collected {series.collected_at.date().isoformat()}"
)
st.info("Data-quality preview only — not a market score, prediction, or investment signal.")

