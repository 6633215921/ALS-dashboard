"""ALS progress viewer: ALSFRS-R total for one patient, coloured by treatment,
with linear slopes in ALSFRS-R points per month.

Data: raw_data.xlsx in the same folder
    - sheet score_timeline : one row per patient per month: id, date, q1..q12, sum_score,
                             source (raw / interpolated), point_type, treatment, on_treatment, month_no
    - sheet raw_data       : riluzole_start/stop, edaravone_start/stop (MM/YYYY) for the drug markers
The workbook's formulas build score_timeline, so open and save raw_data.xlsx in Excel after editing it.

Between raw points (sidebar; used for the chart and the slopes):
  Linear (default) = straight line between raw points, the same as Excel score_timeline / raw_data slopes.
  Step             = hold the last raw score until the next change.
  None             = raw points only (no filled months).
Raw points = filled circles with the score; filled months = small open circles.

Run:  streamlit run visualization.py      (or double-click run_visualization.bat)
"""
from pathlib import Path
import re

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DEFAULT_XLSX = Path(__file__).with_name("raw_data.xlsx")

# Treatment colours: grey = no drug, a hue per drug state (blue / orange / aqua validated as a
# colour-blind-safe set). "off treatment" is grey + dotted so it differs from "before" by pattern.
TREATMENT_STYLE = {
    "before treatment":      ("#8a8984", "solid"),
    "Riluzole":              ("#2a78d6", "solid"),
    "Edaravone":             ("#eb6834", "solid"),
    "Riluzole + Edaravone":  ("#1baf7a", "solid"),
    "off treatment":         ("#8a8984", "dot"),
    "no treatment recorded": ("#8a8984", "solid"),
}
ON_TREATMENT = {"Riluzole", "Edaravone", "Riluzole + Edaravone"}
INK, INK_2, GRID = "#0b0b0b", "#52514e", "#e8e7e3"
RED, GREEN = "#d62728", "#2ca02c"
ITEM_COLS = ["q1_Speech", "q2_Salivation", "q3_Swallowing", "q4_Handwriting", "q5_Cutting_Food",
             "q6_Dressing_and_Hygiene", "q7_Turning_in_Bed", "q8_Walking", "q9_Climbing_Stairs",
             "q10_Dyspnea", "q11_Orthopnea", "q12_Respiratory_Insufficiency"]
SELECTION = "#6250d6"
UNIT = "points/month"
UNIT_HELP = ("Linear regression of the ALSFRS-R total on time. Unit: ALSFRS-R points per month. "
             "-1.00 = losing about 1 point a month (about 12 a year). Closer to 0 = slower decline.")


# ----------------------------------------------------------------------------- helpers
def month_no(ts: pd.Timestamp) -> int:
    return ts.year * 12 + ts.month


def month_ts(m: int) -> pd.Timestamp:
    return pd.Timestamp(year=(m - 1) // 12, month=(m - 1) % 12 + 1, day=1)


def parse_mm_yyyy(value):
    """'03/2026' -> month number, anything else -> None."""
    m = re.fullmatch(r"\s*(\d{1,2})/(\d{4})\s*", str(value)) if pd.notna(value) else None
    return int(m.group(2)) * 12 + int(m.group(1)) if m and 1 <= int(m.group(1)) <= 12 else None


def fit(points: pd.DataFrame):
    """Least-squares slope (points/month) and intercept; None if < 2 distinct months."""
    if len(points) < 2 or points["month_no"].nunique() < 2:
        return None
    slope, intercept = np.polyfit(points["month_no"].astype(float), points["sum_score"].astype(float), 1)
    return float(slope), float(intercept), len(points)


def patient_sort_key(pid: str):
    digits = re.findall(r"\d+", str(pid))
    return (int(digits[0]) if digits else 10**9, str(pid))


@st.cache_data(show_spinner=False)
def load(path: str, mtime: float):
    monthly = pd.read_excel(path, sheet_name="score_timeline", usecols="A:T")
    if "source" not in monthly.columns:
        raise ValueError("score_timeline has no 'source' column - this app needs the updated raw_data.xlsx "
                         "(score_timeline = one row per patient per month).")
    monthly = monthly[monthly["id"].notna() & (monthly["id"].astype(str).str.strip() != "")].copy()
    monthly["id"] = monthly["id"].astype(str).str.strip()
    monthly["date"] = pd.to_datetime(monthly["date"])
    monthly["month_no"] = monthly["date"].map(month_no)
    for col in VALUE_COLS:
        monthly[col] = pd.to_numeric(monthly[col])
    monthly["treatment"] = monthly["treatment"].fillna("no treatment recorded")
    monthly["point_type"] = monthly["point_type"].fillna("")
    drug_cols = ["patient_id", "riluzole_start", "riluzole_stop", "edaravone_start", "edaravone_stop"]
    drugs = pd.read_excel(path, sheet_name="raw_data", dtype=str)
    drugs = drugs[[c for c in drug_cols if c in drugs.columns]]
    drugs = drugs[drugs["patient_id"].notna()].copy()
    drugs["patient_id"] = drugs["patient_id"].str.strip()
    return monthly, drugs


def slope_text(subset: pd.DataFrame, result, filled_word="interpolated"):
    """Value and caption for a slope metric; counts raw and interpolated points separately."""
    if result is None:
        return "–", "needs at least 2 months"
    slope, _, n = result
    n_raw = int((subset["source"] == "raw").sum())
    n_int = n - n_raw
    note = f"{UNIT} · {n_raw} raw" + (f" + {n_int} {filled_word}" if n_int else "") + " points"
    if n_raw < 2:
        note += f" · from {filled_word} months only"
    elif n_raw < 3:
        note += " · fewer than 3 raw points, not reliable"
    return f"{slope:+.2f}", note


LINEAR, STEP, NONE = "Linear (same as Excel)", "Step (hold last score)", "None (raw points only)"
VALUE_COLS = ITEM_COLS + ["sum_score"]


def build_grid(months: pd.DataFrame, raw: pd.DataFrame, method: str) -> pd.DataFrame:
    """Monthly points for one patient. months = all score_timeline rows of the patient (Excel),
    raw = its raw rows. Linear = np.interp between raw points (identical to Excel), Step = hold the last
    raw value, None = raw rows only. Treatment labels always come from Excel."""
    if method == NONE:
        return raw.copy()
    grid = months.copy()
    xs = raw["month_no"].to_numpy(float)
    for col in VALUE_COLS:
        ys = raw[col].to_numpy(float)
        if method == LINEAR:
            grid[col] = np.interp(grid["month_no"].to_numpy(float), xs, ys)
        else:
            idx = np.searchsorted(xs, grid["month_no"].to_numpy(float), side="right") - 1
            grid[col] = ys[np.clip(idx, 0, len(ys) - 1)]
    return grid


# ----------------------------------------------------------------------------- page
st.set_page_config(page_title="ALS progress", layout="wide")
st.title("ALSFRS-R")

with st.sidebar:
    xlsx = st.text_input("Workbook", str(DEFAULT_XLSX))
    if not Path(xlsx).is_file():
        st.error(f"File not found: {xlsx}")
        st.stop()
    try:
        timeline, drugs = load(xlsx, Path(xlsx).stat().st_mtime)
    except ValueError as err:
        st.error(str(err))
        st.stop()
    if timeline.empty:
        st.error("score_timeline has no rows. Open raw_data.xlsx in Excel, let it calculate, "
                 "save, then reload this page.")
        st.stop()

    ids = sorted(timeline["id"].unique(), key=patient_sort_key)
    pid = st.selectbox("Patient ID", ids)

    months_df = timeline[timeline["id"] == pid].sort_values("month_no").reset_index(drop=True)
    pts = months_df[months_df["source"] == "raw"].reset_index(drop=True)      # raw points
    first_m, last_m = int(months_df["month_no"].min()), int(months_df["month_no"].max())
    month_options = list(range(first_m, last_m + 1))
    if len(month_options) >= 2:
        start_m, end_m = st.select_slider(
            "Time of interest", options=month_options, value=(first_m, last_m),
            format_func=lambda m: month_ts(m).strftime("%b %Y"), key=f"range_{pid}")
    else:
        start_m = end_m = first_m

    st.markdown("**Show on chart**")
    show_all = st.checkbox("Slope, all points", value=False)
    show_before = st.checkbox("Slope, before treatment", value=False)
    show_on = st.checkbox("Slope, on treatment", value=False)
    show_range = st.checkbox("Slope, time of interest", value=False)
    show_drugs = st.checkbox("Drug start / stop markers", value=True)
    method = st.radio(
        "Between raw points (chart and slopes)", [LINEAR, STEP, NONE], index=0,
        help="Linear: straight line between raw points - the same as Excel (score_timeline and the raw_data "
             "slopes). Step: the score stays at the last raw value until the next change. None: raw points "
             "only, so slopes use months with a change only and a time of interest needs 2 raw points.")
    show_interp = st.checkbox("Show interpolated data (open circles)", value=True, disabled=method == NONE)
    if st.button("Reload workbook"):
        load.clear()
        st.rerun()

# ----------------------------------------------------------------------------- data + slopes
drug_row = (drugs[drugs["patient_id"] == pid].iloc[0]
            if not drugs.empty and pid in set(drugs["patient_id"]) else None)
grid = build_grid(months_df, pts, method)
data = grid                                   # points used for the line and every slope
step_line = method == STEP

sub_all = data
sub_before = data[data["treatment"] == "before treatment"]
sub_on = data[data["treatment"].isin(ON_TREATMENT)]
in_range = data[(data["month_no"] >= start_m) & (data["month_no"] <= end_m)]
fit_all, fit_before, fit_on, fit_range = (fit(d) for d in (sub_all, sub_before, sub_on, in_range))

latest = pts.iloc[-1]
c0, c1, c2, c3, c4 = st.columns(5)
c0.metric("Latest ALSFRS-R", f"{int(latest['sum_score'])} / 48",
          help=f"{latest['date']:%b %Y} · {latest['treatment']}")
for col, label, subset, result, extra in (
        (c1, "slope_all", sub_all, fit_all, ""),
        (c2, "slope_before", sub_before, fit_before, ""),
        (c3, "slope_on_treatment", sub_on, fit_on, ""),
        (c4, "slope, time of interest", in_range, fit_range,
         f"{month_ts(start_m):%b %Y} – {month_ts(end_m):%b %Y} · ")):
    value, note = slope_text(subset, result, "filled" if method == STEP else "interpolated")
    col.metric(label, value, help=UNIT_HELP)
    col.caption(extra + note)

# ----------------------------------------------------------------------------- chart
fig = go.Figure()
if show_range and (start_m, end_m) != (first_m, last_m):
    fig.add_vrect(x0=month_ts(start_m), x1=month_ts(end_m), fillcolor=SELECTION, opacity=0.07,
                  line_width=0, layer="below")

shown = set()
line_pts = grid                               # 1) line coloured by treatment (month by month)
runs = []                                     # consecutive segments with the same treatment
for i in range(1, len(line_pts)):
    a, b = line_pts.iloc[i - 1], line_pts.iloc[i]
    xs, ys = [a["date"], b["date"]], [a["sum_score"], b["sum_score"]]
    if step_line:
        xs, ys = [a["date"], b["date"], b["date"]], [a["sum_score"], a["sum_score"], b["sum_score"]]
    if runs and runs[-1]["label"] == b["treatment"]:
        runs[-1]["x"] += xs[1:]
        runs[-1]["y"] += ys[1:]
    else:
        runs.append({"label": b["treatment"], "x": xs, "y": ys})
for run in runs:
    colour, dash = TREATMENT_STYLE.get(run["label"], ("#8a8984", "solid"))
    fig.add_trace(go.Scatter(x=run["x"], y=run["y"], mode="lines",
                             line=dict(color=colour, width=2.5, dash=dash),
                             name=run["label"], legendgroup=run["label"],
                             showlegend=run["label"] not in shown, hoverinfo="skip"))
    shown.add(run["label"])

if show_interp and method != NONE:            # filled months: small open circles, no value label
    interp = grid[grid["source"] == "interpolated"]
    for label, group in interp.groupby("treatment", sort=False):
        colour, _ = TREATMENT_STYLE.get(label, ("#8a8984", "solid"))
        fig.add_trace(go.Scatter(
            x=group["date"], y=group["sum_score"], mode="markers", name=label, legendgroup=label,
            showlegend=False,
            marker=dict(symbol="circle-open", size=7, color=colour, line=dict(width=1.5)),
            customdata=group[["treatment"]].to_numpy(),
            hovertemplate=("%{x|%b %Y}<br>%{y:.0f} / 48 · filled (step: held from the last raw point)"
                           if step_line else "%{x|%b %Y}<br>≈ %{y:.1f} / 48 · interpolated (linear)")
                          + "<br>%{customdata[0]}<extra></extra>"))

for label, group in pts.groupby("treatment", sort=False):
    colour, _ = TREATMENT_STYLE.get(label, ("#8a8984", "solid"))
    fig.add_trace(go.Scatter(
        x=group["date"], y=group["sum_score"], name=label, legendgroup=label,
        showlegend=label not in shown,
        marker=dict(size=9, color=colour, line=dict(color="white", width=2)),
        
        mode="markers+text",                          # Changed mode to include text
        text=group["sum_score"].astype(int),          # Show the sum_score value
        textposition="top center",                    # Position the text above the marker
        textfont=dict(size=11, color=INK_2),          # Styling for the label text
        
        customdata=np.stack([group["treatment"], group["point_type"]], axis=-1),
        hovertemplate="%{x|%b %Y}<br>ALSFRS-R <b>%{y}</b> / 48<br>%{customdata[0]} · %{customdata[1]}"
                      "<extra></extra>"))
    shown.add(label)


def draw_fit(subset, result, name, colour, dash, width):
    if result is None:
        return
    slope, intercept, n = result
    x0, x1 = int(subset["month_no"].min()), int(subset["month_no"].max())
    fig.add_trace(go.Scatter(
        x=[month_ts(x0), month_ts(x1)], y=[intercept + slope * x0, intercept + slope * x1],
        mode="lines", line=dict(color=colour, width=width, dash=dash),
        name=f"{name}: {slope:+.2f} {UNIT}",
        hovertemplate=f"{name}<br>{slope:+.2f} {UNIT} · {n} points "
                      f"({int((subset['source'] == 'raw').sum())} raw)<extra></extra>"))


if show_all:
    draw_fit(sub_all, fit_all, "Slope, all points", INK, "dot", 3)
if show_before:
    draw_fit(sub_before, fit_before, "Slope, before treatment", RED, "dot", 3)
if show_on:
    draw_fit(sub_on, fit_on, "Slope, on treatment", GREEN, "dot", 3)
if show_range:
    draw_fit(in_range, fit_range, "Slope, time of interest", SELECTION, "dot", 3)

if show_drugs and drug_row is not None:
    row = drug_row
    marks = [("riluzole_start", "Riluzole start", "Riluzole"), ("riluzole_stop", "Riluzole stop", "Riluzole"),
             ("edaravone_start", "Edaravone start", "Edaravone"), ("edaravone_stop", "Edaravone stop", "Edaravone")]
    used = {}
    for col, text, drug in marks:
        m = parse_mm_yyyy(row.get(col))
        if m is None:
            continue
        level = used.get(m, 0)
        used[m] = level + 1
        fig.add_vline(x=month_ts(m), line=dict(color=TREATMENT_STYLE[drug][0], width=1, dash="dot"))
        fig.add_annotation(x=month_ts(m), y=1.0 - 0.06 * level, yref="paper", text=text, showarrow=False,
                           xanchor="left", yanchor="top", xshift=4, font=dict(size=11, color=INK_2))

fig.update_layout(
    template="plotly_white", height=580, margin=dict(l=10, r=10, t=40, b=10),
    hovermode="closest", font=dict(color=INK, size=13),
    title=dict(text=f"{pid} · ALSFRS-R total", x=0, font=dict(size=16)),
    legend=dict(orientation="h", yanchor="top", y=-0.08, xanchor="left", x=0, title_text=""),
)
fig.update_yaxes(title_text="ALSFRS-R total (0–48)", range=[0, 49], dtick=6, gridcolor=GRID,
                 zeroline=False)
fig.update_xaxes(title_text="", tickformat="%b %Y", gridcolor=GRID, showgrid=False)

# marker legend: raw vs interpolated
fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers", name="Raw data (form)",
                         marker=dict(symbol="circle", size=9, color=INK_2, line=dict(color="white", width=2))))
if show_interp and method != NONE:
    fig.add_trace(go.Scatter(x=[None], y=[None], mode="markers",
                             name="Filled month (step)" if step_line else "Interpolated month (linear)",
                             marker=dict(symbol="circle-open", size=7, color=INK_2, line=dict(width=1.5))))

st.plotly_chart(fig, theme=None)

st.caption("Filled circles are raw points: a month in which at least one ALSFRS-R item changed level on "
           "the form (plus the optional 48 baseline and the last assessment). Open circles fill the months in "
           "between: Linear puts them on the straight line between two raw points (the same as Excel); Step "
           "holds the last raw score; None shows raw points only. The line is coloured by the drug(s) taken in "
           "each month. Slopes are least-squares lines through the points shown, in ALSFRS-R points per month; "
           "with Linear they equal the slopes in raw_data. Check the raw-point count under each slope: fewer "
           "than 3 raw points is not reliable, and one patient's flatter slope is consistent with, but does not "
           "prove, a treatment effect.")

with st.expander("Points for this patient (table view)"):
    items = [c for c in pts.columns if re.match(r"q\d+_", str(c))]
    table = grid[["date", "sum_score", "treatment", "source", "point_type"] + items].copy()
    table[items] = table[items].round(2)
    table["sum_score"] = table["sum_score"].round(2)
    table["date"] = table["date"].dt.strftime("%m/%Y")
    st.dataframe(table, hide_index=True)
