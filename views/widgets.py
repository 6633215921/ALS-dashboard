"""Widgets used on several pages, and the settings at the bottom of the sidebar."""
from __future__ import annotations

import streamlit as st

from als import storage
from als.model import OPTIONAL_MONTH_PATTERN
from views import data, state

NEW_PATIENT = "+ New patient"
MONTH_HELP = "MM/YYYY in AD, e.g. 03/2026"


def pick_patient(ids: list[str], key: str, allow_new: bool = False, label: str = "Patient ID") -> str:
    """Patient selector; the choice is shared between pages (state.PATIENT)."""
    options = ([NEW_PATIENT] if allow_new else []) + ids
    current = state.selected_patient()
    index = options.index(current) if current in options else (1 if allow_new and ids else 0)
    choice = st.selectbox(label, options, index=index, key=f"{key}_{state.editor_version()}")
    if choice != NEW_PATIENT:
        state.select_patient(choice)
    return choice


def course_columns(type_names: list[str]) -> dict:
    """Column settings of the treatment-course editors (Patient form and Treatments pages)."""
    return {
        "treatment": st.column_config.SelectboxColumn("Treatment", options=type_names, required=True),
        "start": st.column_config.TextColumn("Start (MM/YYYY)", help=MONTH_HELP, required=True,
                                             validate=OPTIONAL_MONTH_PATTERN),
        "stop": st.column_config.TextColumn("Stop (MM/YYYY)", help=MONTH_HELP + ". Blank = still on.",
                                            validate=OPTIONAL_MONTH_PATTERN),
        "notes": st.column_config.TextColumn("Notes"),
    }


def sidebar_footer() -> None:
    """Settings and data-file notes used by every page, at the bottom of the sidebar."""
    with st.sidebar:
        st.divider()
        st.checkbox("Add 48 baseline (1 month before the first change)", key=state.BASELINE,
                    help="Adds a raw point of 48/48 one month before the first dated box. Used by every page.")
        # A click reruns the page, and data.sync() then picks up any change made in Excel.
        st.button("Reload data", help="Show changes saved in Excel. The app also checks on every click.")
        st.caption(f"Data file: {data.DATA_FILE}")
        if storage.open_in_excel(data.DATA_FILE):
            st.info(f"{data.DATA_FILE.name} seems to be open in Excel. The app can save only after it is closed "
                    "there; Excel's changes show here once Excel has saved them.")
        if data.is_sample_data(data.load_tables()):
            st.warning("Sample data: these are DUMMY patients. Before entering real patients, start empty: "
                       f"All patients & data → Upload data → {data.SAMPLE_DIR.name}/{data.BLANK_FILE.name}.")
        if data.on_streamlit_cloud():
            st.warning("Edits are saved on the app server only and are lost when the app restarts. "
                       "Download a copy after editing (All patients & data).")
