"""Dashboard page: ALSFRS-R total of one patient over time, coloured by treatment, slopes in points/month."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from als.model import FORMS, ITEMS, TREATMENTS, TYPES, form_row, format_month, month_start, patient_ids, treatment_names
from als.scoring import LINEAR, RAW_ONLY, STEP, fit, monthly, patient_courses, raw_points, slope_groups
from views import chart
from views.chart import SLOPE_LINES, UNIT, ChartOptions
from views.shared import baseline_on, editor_version, load_tables, pick_patient

METHODS = {"Linear (default)": LINEAR, "Step (hold last score)": STEP, "None (raw points only)": RAW_ONLY}
METHOD_HELP = ("Linear: straight line between raw points - the base for the slopes on every page. Step: the score "
               "stays at the last raw value until the next change. None: raw points only, so slopes use months "
               "with a change only and a time of interest needs 2 raw points.")
UNIT_HELP = ("Linear regression of the ALSFRS-R total on time. Unit: ALSFRS-R points per month. "
             "-1.00 = losing about 1 point a month (about 12 a year). Closer to 0 = slower decline.")
CAPTION = ("Filled circles are raw points: a month in which at least one ALSFRS-R item changed level on the form "
           "(plus the optional 48 baseline and the last assessment). Open circles fill the months in between: Linear "
           "puts them on the straight line between two raw points; Step holds the last raw score; None shows raw "
           "points only. The line is coloured by the drug(s) taken in each month. Slopes are least-squares lines "
           "through the points shown, in ALSFRS-R points per month; with Linear they equal the slopes on the All "
           "patients page. Check the raw-point count under each slope: fewer than 3 raw points is not reliable, and "
           "one patient's flatter slope is consistent with, but does not prove, a treatment effect.")


def render() -> None:
    st.title("ALSFRS-R")
    tables = load_tables()
    ids = patient_ids(tables[FORMS])
    if not ids:
        st.info("No patients yet. Add one on the Patient form page, or upload a workbook on All patients & data.")
        return
    baseline = baseline_on()
    with st.sidebar:
        pid = pick_patient(ids, key="pick_dash")
        points = raw_points(form_row(tables, pid), baseline)
        if points.empty:
            st.warning(f"{pid} has no month in any box yet.")
            return
        opts = _sidebar_options(pid, points, baseline)

    courses = patient_courses(tables[TREATMENTS], pid)
    order = treatment_names(tables[TYPES])
    grid = monthly(points, courses, order, opts.method)
    grid["date"] = grid["month_no"].map(month_start)
    groups = slope_groups(grid, opts.time_of_interest)
    fits = {key: fit(subset) for key, subset in groups.items()}

    _metrics(grid, groups, fits, opts)
    st.plotly_chart(chart.figure(pid, grid, courses, order, opts, groups, fits), theme=None)
    st.caption(CAPTION)
    _slope_by_state(grid)
    _points_table(grid)


def _sidebar_options(pid: str, points: pd.DataFrame, baseline: bool) -> ChartOptions:
    first, last = int(points["month_no"].min()), int(points["month_no"].max())
    if last > first:
        start, end = st.select_slider(
            "Time of interest", options=list(range(first, last + 1)), value=(first, last),
            format_func=lambda m: month_start(m).strftime("%b %Y"),
            key=f"range_{pid}_{baseline}_{editor_version()}")
    else:
        start = end = first
    st.markdown("**Show on chart**")
    slopes = tuple(line.key for line in SLOPE_LINES if st.checkbox(line.name, value=False))
    show_drugs = st.checkbox("Drug start / stop markers", value=True)
    method = METHODS[st.radio("Between raw points (chart and slopes)", list(METHODS), index=0, help=METHOD_HELP)]
    show_interpolated = st.checkbox("Show interpolated data (open circles)", value=True, disabled=method == RAW_ONLY)
    return ChartOptions(method=method, time_of_interest=(start, end), full_range=(first, last), slopes=slopes,
                        show_drugs=show_drugs, show_interpolated=show_interpolated)


def _metrics(grid, groups, fits, opts: ChartOptions) -> None:
    latest = grid[grid["source"] == "raw"].iloc[-1]
    columns = st.columns(1 + len(SLOPE_LINES))
    columns[0].metric("Latest ALSFRS-R", f"{int(latest['sum_score'])} / 48",
                      help=f"{latest['date']:%b %Y} · {latest['treatment']}")
    filled_word = "filled" if opts.step else "interpolated"
    for col, line in zip(columns[1:], SLOPE_LINES, strict=True):
        value, note = _slope_text(groups[line.key], fits[line.key], filled_word)
        if line.key == "range":
            start, end = opts.time_of_interest
            note = f"{month_start(start):%b %Y} – {month_start(end):%b %Y} · " + note
        col.metric(line.metric, value, help=UNIT_HELP)
        col.caption(note)


def _slope_text(subset: pd.DataFrame, result, filled_word: str) -> tuple[str, str]:
    """Metric value and caption; counts raw and filled points separately and flags unreliable slopes."""
    if result is None:
        return "–", "needs at least 2 months"
    n_raw = int((subset["source"] == "raw").sum())
    n_filled = result.n - n_raw
    note = f"{UNIT} · {n_raw} raw" + (f" + {n_filled} {filled_word}" if n_filled else "") + " points"
    if n_raw < 2:
        note += f" · from {filled_word} months only"
    elif n_raw < 3:
        note += " · fewer than 3 raw points, not reliable"
    return f"{round(result.slope, 2) + 0.0:+.2f}", note


def _slope_by_state(grid: pd.DataFrame) -> None:
    with st.expander("Slope by treatment state"):
        rows = []
        for label, group in grid.groupby("treatment", sort=False):
            result = fit(group)
            rows.append({"treatment": label,
                         "from": format_month(group["month_no"].min()), "to": format_month(group["month_no"].max()),
                         "months": len(group), "raw points": int((group["source"] == "raw").sum()),
                         f"slope ({UNIT})": None if result is None else round(result.slope, 2) + 0.0})
        st.dataframe(pd.DataFrame(rows), hide_index=True, column_config={
            "treatment": st.column_config.TextColumn("treatment", width="large"),
            f"slope ({UNIT})": st.column_config.NumberColumn(f"slope ({UNIT})", format="%+.2f")})
        st.caption("Each row fits only the months with that exact drug state (e.g. Riluzole alone vs. Riluzole + "
                   "Edaravone). Short states with fewer than 3 raw points are not reliable.")


def _points_table(grid: pd.DataFrame) -> None:
    with st.expander("Points for this patient (table view)"):
        table = grid[["date", "sum_score", "treatment", "source", "point_type", *ITEMS]].copy()
        table[[*ITEMS, "sum_score"]] = table[[*ITEMS, "sum_score"]].round(2)
        table["date"] = table["date"].dt.strftime("%m/%Y")
        st.dataframe(table, hide_index=True)
