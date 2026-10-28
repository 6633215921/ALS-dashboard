"""The Dashboard chart (Plotly): ALSFRS-R total over time, coloured by treatment, with slope lines."""
from __future__ import annotations

import zlib
from dataclasses import dataclass
from typing import NamedTuple

import numpy as np
import pandas as pd
import plotly.graph_objects as go

from als.model import month_start
from als.scoring import RAW_ONLY, STEP, Course, Fit, rounded

# Treatment colours: grey = no drug, a hue per drug state (blue / orange / aqua validated as a colour-blind-safe
# set). "off treatment" is grey + dotted so it differs from "before" by pattern. Treatment types added later get
# the next colour in DRUG_COLOURS (by their order on the Treatments page); combinations get a COMBO_COLOURS hue.
TREATMENT_STYLE = {
    "before treatment":      ("#8a8984", "solid"),
    "Riluzole":              ("#2a78d6", "solid"),
    "Edaravone":             ("#eb6834", "solid"),
    "Riluzole + Edaravone":  ("#1baf7a", "solid"),
    "off treatment":         ("#8a8984", "dot"),
    "no treatment recorded": ("#8a8984", "solid"),
}
DRUG_COLOURS = ["#2a78d6", "#eb6834", "#c2489a", "#9a6b2f", "#127a8a", "#b8a01c", "#e377c2", "#5c6bc0"]
COMBO_COLOURS = ["#1baf7a", "#8e5ea2", "#b0563a", "#3b6e8f", "#7d8c2a", "#d17a9f"]
INK, INK_2, GRID = "#0b0b0b", "#52514e", "#e8e7e3"
RED, GREEN, SELECTION = "#d62728", "#2ca02c", "#6250d6"
UNIT = "points/month"


class SlopeLine(NamedTuple):
    key: str                        # group in als.scoring.slope_groups
    metric: str                     # metric label above the chart
    name: str                       # checkbox label and legend name
    colour: str


SLOPE_LINES = [
    SlopeLine("all", "slope_all", "Slope, all points", INK),
    SlopeLine("before", "slope_before", "Slope, before treatment", RED),
    SlopeLine("on", "slope_on_treatment", "Slope, on treatment", GREEN),
    SlopeLine("range", "slope, time of interest", "Slope, time of interest", SELECTION),
]


@dataclass(frozen=True, eq=False)
class PatientChart:
    """One patient's data as the Dashboard shows it."""
    pid: str
    grid: pd.DataFrame                      # monthly timeline (als.scoring.monthly) with a 'date' column
    courses: list[Course]
    order: list[str]                        # treatment types in list order: drug colours and 'A + B' labels
    groups: dict[str, pd.DataFrame]         # months of each slope (als.scoring.slope_groups)
    fits: dict[str, Fit | None]             # the fit of each group


@dataclass
class ChartOptions:
    method: str                             # als.scoring LINEAR / STEP / RAW_ONLY
    time_of_interest: tuple[int, int]       # month numbers
    full_range: tuple[int, int]             # first and last raw month
    slopes: tuple[str, ...] = ()            # SLOPE_LINES keys to draw
    show_drugs: bool = True
    show_interpolated: bool = True

    @property
    def step(self) -> bool:
        return self.method == STEP

    @property
    def open_circles(self) -> bool:
        return self.show_interpolated and self.method != RAW_ONLY


def style(label: str, order: list[str]) -> tuple[str, str]:
    """(colour, dash) for a treatment label such as 'Riluzole' or 'Riluzole + Nusinersen'."""
    if label in TREATMENT_STYLE:
        return TREATMENT_STYLE[label]
    if label in order:
        return DRUG_COLOURS[order.index(label) % len(DRUG_COLOURS)], "solid"
    return COMBO_COLOURS[zlib.crc32(label.encode()) % len(COMBO_COLOURS)], "solid"


def figure(data: PatientChart, opts: ChartOptions) -> go.Figure:
    """The Dashboard chart of one patient."""
    grid, order = data.grid, data.order
    fig = go.Figure()
    if "range" in opts.slopes and opts.time_of_interest != opts.full_range:
        start, end = opts.time_of_interest
        fig.add_vrect(x0=month_start(start), x1=month_start(end), fillcolor=SELECTION, opacity=0.07,
                      line_width=0, layer="below")
    in_legend: set[str] = set()
    _treatment_line(fig, grid, order, opts.step, in_legend)
    if opts.open_circles:
        _interpolated_points(fig, grid[grid["source"] == "interpolated"], order, opts.step)
    _raw_points(fig, grid[grid["source"] == "raw"], order, in_legend)
    for line in SLOPE_LINES:
        if line.key in opts.slopes:
            _slope_line(fig, data.groups[line.key], data.fits[line.key], line)
    if opts.show_drugs:
        _drug_markers(fig, data.courses, order)
    _layout(fig, data.pid)
    _marker_legend(fig, opts)
    return fig


# ----------------------------------------------------------------------------- traces
def _treatment_line(fig, grid, order, step, in_legend):
    """The score line, one trace per run of months with the same treatment."""
    runs = []
    for i in range(1, len(grid)):
        a, b = grid.iloc[i - 1], grid.iloc[i]
        xs, ys = [a["date"], b["date"]], [a["sum_score"], b["sum_score"]]
        if step:
            xs, ys = [a["date"], b["date"], b["date"]], [a["sum_score"], a["sum_score"], b["sum_score"]]
        if runs and runs[-1]["label"] == b["treatment"]:
            runs[-1]["x"] += xs[1:]
            runs[-1]["y"] += ys[1:]
        else:
            runs.append({"label": b["treatment"], "x": xs, "y": ys})
    for run in runs:
        colour, dash = style(run["label"], order)
        fig.add_trace(go.Scatter(x=run["x"], y=run["y"], mode="lines",
                                 line=dict(color=colour, width=2.5, dash=dash),
                                 name=run["label"], legendgroup=run["label"],
                                 showlegend=run["label"] not in in_legend, hoverinfo="skip"))
        in_legend.add(run["label"])


def _interpolated_points(fig, points, order, step):
    """Filled months: small open circles, no value label."""
    hover = ("%{x|%b %Y}<br>%{y:.0f} / 48 · filled (step: held from the last raw point)" if step
             else "%{x|%b %Y}<br>≈ %{y:.1f} / 48 · interpolated (linear)")
    for label, group in points.groupby("treatment", sort=False):
        colour, _ = style(label, order)
        fig.add_trace(go.Scatter(
            x=group["date"], y=group["sum_score"], mode="markers", name=label, legendgroup=label,
            showlegend=False,
            marker=dict(symbol="circle-open", size=7, color=colour, line=dict(width=1.5)),
            customdata=group[["treatment"]].to_numpy(),
            hovertemplate=hover + "<br>%{customdata[0]}<extra></extra>"))


def _raw_points(fig, points, order, in_legend):
    """Raw points: filled circles with the score above."""
    for label, group in points.groupby("treatment", sort=False):
        colour, _ = style(label, order)
        fig.add_trace(go.Scatter(
            x=group["date"], y=group["sum_score"], name=label, legendgroup=label,
            showlegend=label not in in_legend,
            marker=dict(size=9, color=colour, line=dict(color="white", width=2)),
            mode="markers+text",
            text=group["sum_score"].astype(int),
            textposition="top center",
            textfont=dict(size=11, color=INK_2),
            customdata=np.stack([group["treatment"], group["point_type"]], axis=-1),
            hovertemplate="%{x|%b %Y}<br>ALSFRS-R <b>%{y}</b> / 48<br>%{customdata[0]} · %{customdata[1]}"
                          "<extra></extra>"))
        in_legend.add(label)


def _slope_line(fig, subset, result, line: SlopeLine):
    if result is None:
        return
    slope = rounded(result)
    x0, x1 = int(subset["month_no"].min()), int(subset["month_no"].max())
    n_raw = int((subset["source"] == "raw").sum())
    fig.add_trace(go.Scatter(
        x=[month_start(x0), month_start(x1)],
        y=[result.intercept + result.slope * x0, result.intercept + result.slope * x1],
        mode="lines", line=dict(color=line.colour, width=3, dash="dot"),
        name=f"{line.name}: {slope:+.2f} {UNIT}",
        hovertemplate=f"{line.name}<br>{slope:+.2f} {UNIT} · {result.n} points ({n_raw} raw)<extra></extra>"))


def _drug_markers(fig, courses, order):
    """A dotted line + label at every course start / stop; labels less than 5 months apart are stacked."""
    marks = sorted([(c.start, f"{c.treatment} start", c.treatment) for c in courses] +
                   [(c.stop, f"{c.treatment} stop", c.treatment) for c in courses if c.stop is not None])
    placed = []                                     # (month, label row)
    for m, text, drug in marks:
        row = 0
        while any(r == row and abs(m - pm) < 5 for pm, r in placed):
            row += 1
        placed.append((m, row))
        fig.add_vline(x=month_start(m), line=dict(color=style(drug, order)[0], width=1, dash="dot"))
        fig.add_annotation(x=month_start(m), y=1.0 - 0.06 * row, yref="paper", text=text, showarrow=False,
                           xanchor="left", yanchor="top", xshift=4, font=dict(size=11, color=INK_2))


def _layout(fig, pid):
    fig.update_layout(
        template="plotly_white", height=580, margin=dict(l=10, r=10, t=40, b=10),
        hovermode="closest", font=dict(color=INK, size=13),
        title=dict(text=f"{pid} · ALSFRS-R total", x=0, font=dict(size=16)),
        legend=dict(orientation="h", yanchor="top", y=-0.08, xanchor="left", x=0, title_text=""),
    )
    fig.update_yaxes(title_text="ALSFRS-R total (0–48)", range=[0, 49], dtick=6, gridcolor=GRID, zeroline=False)
    fig.update_xaxes(title_text="", tickformat="%b %Y", gridcolor=GRID, showgrid=False)


def _marker_legend(fig, opts: ChartOptions):
    """Legend entries for the two marker shapes: raw vs interpolated."""
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name="Raw data (form)",
                             marker=dict(symbol="circle", size=9, color=INK_2, line=dict(color="white", width=2))))
    if opts.open_circles:
        fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers",
                                 name="Filled month (step)" if opts.step else "Interpolated month (linear)",
                                 marker=dict(symbol="circle-open", size=7, color=INK_2, line=dict(width=1.5))))
