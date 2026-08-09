"""Pure presentation helpers for market-series data previews."""

from dataclasses import dataclass
from statistics import fmean

import plotly.graph_objects as go

from market_intelligence_lab.collection.models import SeriesData


@dataclass(frozen=True, slots=True)
class SeriesSummary:
    latest: float
    previous_change: float
    historical_mean: float


def summarize(data: SeriesData) -> SeriesSummary:
    if len(data.observations) < 2:
        raise ValueError("At least two observations are required for a preview")
    values = [observation.value for observation in data.observations]
    return SeriesSummary(
        latest=values[-1],
        previous_change=values[-1] - values[-2],
        historical_mean=fmean(values),
    )


def build_figure(
    data: SeriesData,
    historical_mean: float,
    yaxis_title: str,
) -> go.Figure:
    figure = go.Figure(
        go.Scatter(
            x=[observation.date for observation in data.observations],
            y=[observation.value for observation in data.observations],
            mode="lines",
            name=data.series_id,
            line={"color": "#2563eb", "width": 2},
        )
    )
    figure.add_hline(
        y=historical_mean,
        line_dash="dot",
        line_color="#94a3b8",
        annotation_text="Historical mean",
    )
    figure.update_layout(
        margin={"l": 0, "r": 0, "t": 30, "b": 0},
        height=430,
        hovermode="x unified",
        yaxis_title=yaxis_title,
        xaxis_title=None,
        template="plotly_white",
    )
    return figure

