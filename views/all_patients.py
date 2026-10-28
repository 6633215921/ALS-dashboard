"""All patients & data page: summary of every patient, downloads, and upload (replace all data)."""
from __future__ import annotations

from datetime import date

import streamlit as st

from als.checks import ERROR, validate
from als.model import FORMS, TREATMENTS, TYPES, treatment_names
from als.report import summary, timeline
from als.storage import WorkbookError, read_workbook, to_workbook_bytes
from views import data, state

SLOPE_COLS = ("slope_all", "slope_before", "slope_on_treatment")
SLOPE_HELP = "ALSFRS-R points per month (linear regression on the monthly scores, Linear interpolation)."
XLSX = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


def render() -> None:
    st.title("All patients & data")
    state.show_flash()
    tables = data.load_tables()
    baseline = state.baseline_on()
    table = summary(tables, baseline=baseline)
    _summary_section(tables, table, baseline)
    _download_section(tables, table, baseline)
    _upload_section(tables)


def _summary_section(tables, table, baseline: bool) -> None:
    issues = validate(tables)
    n_errors = sum(1 for i in issues if i.level == ERROR)
    st.caption(f"{len(table)} patients · {len(tables[TREATMENTS])} treatment courses · "
               f"{len(treatment_names(tables[TYPES]))} treatment types · {n_errors} error(s), "
               f"{len(issues) - n_errors} warning(s) (see column check). Slopes use Linear interpolation"
               f"{' and the 48 baseline' if baseline else ''}.")
    columns = {col: st.column_config.NumberColumn(col, format="%+.2f", help=SLOPE_HELP) for col in SLOPE_COLS}
    st.dataframe(table, hide_index=True,
                 column_config={**columns, "check": st.column_config.TextColumn("check", width="large")})


def _download_section(tables, table, baseline: bool) -> None:
    st.subheader("Download")
    months = timeline(tables, baseline=baseline)
    stamp = date.today().isoformat()
    left, right = st.columns(2)
    left.download_button(
        "Workbook: data + results (.xlsx)", on_click="ignore", file_name=f"als_data_{stamp}.xlsx", mime=XLSX,
        data=to_workbook_bytes(tables, results={"summary": table, "score_timeline": months}),
        help="Sheets forms, treatments, treatment_types (the data; can be uploaded again) "
             "+ summary and score_timeline (results, one row per patient per month).")
    right.download_button(
        "score_timeline (.csv)", on_click="ignore", file_name=f"als_score_timeline_{stamp}.csv", mime="text/csv",
        data=months.assign(date=months["date"].dt.strftime("%m/%Y")).to_csv(index=False).encode("utf-8-sig"))


def _upload_section(current) -> None:
    st.subheader("Upload data (replace all data)")
    st.caption("An .xlsx with the sheets forms, treatments and treatment_types: a workbook downloaded above, "
               f"{data.BLANK_FILE.relative_to(data.ROOT)} (start empty) or {data.DUMMY_FILE.relative_to(data.ROOT)} "
               "(22 DUMMY patients for training). It replaces everything in the data file; download a copy first "
               "if you may need the current data again.")
    upload = st.file_uploader("Workbook", type=["xlsx"], label_visibility="collapsed")
    if upload is None:
        return
    try:
        new = read_workbook(upload)
    except WorkbookError as err:
        st.error("This file cannot be used:\n" + "\n".join(f"- {p}" for p in err.problems))
        return
    errors = [i for i in validate(new) if i.level == ERROR]
    st.write(f"File: {len(new[FORMS])} patients, {len(new[TREATMENTS])} treatment courses, "
             f"{len(new[TYPES])} treatment types, {len(errors)} error(s).")
    if errors:
        st.warning("\n".join(f"- {i.patient_id}: {i.message}" for i in errors))
    confirmed = st.checkbox("Yes, replace all current data with this file")
    if st.button("Replace all data", disabled=not confirmed, type="primary"):
        data.save(current, new, f"Data replaced from {upload.name}.", check=False)
