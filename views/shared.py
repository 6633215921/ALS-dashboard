"""Data access and widgets shared by every page."""
from __future__ import annotations

from pathlib import Path

import streamlit as st

from als import storage
from als.checks import error_keys, validate
from als.model import OPTIONAL_MONTH_PATTERN, Tables

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "raw_data.xlsx"
NEW_PATIENT = "+ New patient"
MONTH_HELP = "MM/YYYY in AD, e.g. 03/2026"
_KEEP = object()                                    # save(select=...) default: keep the selected patient


# ----------------------------------------------------------------------------- data
@st.cache_data(ttl=120, show_spinner="Loading data…")
def load_tables() -> Tables:
    """The data, cached for 2 minutes and cleared on every save and by Reload data."""
    return storage.load(DATA_FILE)


def load_latest() -> Tables:
    """Uncached read, used right before a save so the edit is applied to the latest data."""
    return storage.load(DATA_FILE)


def save(before: Tables | None, after: Tables, message: str, select=_KEEP, check: bool = True) -> None:
    """Write the data unless the edit adds an error, then rerun the page with a success message.

    before: the latest data the edit was applied to (to tell new errors from old ones).
    select: patient to select afterwards (None = no patient); leave out to keep the current selection.
    check: False writes without the error check (upload, after the user has seen the errors).
    """
    if check:
        new_errors = error_keys(validate(after)) - error_keys(validate(before))
        if new_errors:
            st.error("Not saved. Please fix:\n" + "\n".join(f"- {pid}: {msg}" for pid, msg in sorted(new_errors)))
            return
    storage.save(DATA_FILE, after)
    load_tables.clear()
    st.session_state.flash = message
    st.session_state.ver = editor_version() + 1     # new widget keys -> editors show the saved data
    if select is not _KEEP:
        st.session_state.pid = select
        st.session_state.pop("pick_form", None)
    st.rerun()


def editor_version() -> int:
    return st.session_state.get("ver", 0)


def show_flash() -> None:
    if message := st.session_state.pop("flash", None):
        st.success(message)


# ----------------------------------------------------------------------------- widgets
def pick_patient(ids: list[str], key: str, allow_new: bool = False, label: str = "Patient ID") -> str:
    """Patient selector; the choice is shared between pages (st.session_state.pid)."""
    options = ([NEW_PATIENT] if allow_new else []) + ids
    current = st.session_state.get("pid")
    index = options.index(current) if current in options else (1 if allow_new and ids else 0)
    choice = st.selectbox(label, options, index=index, key=key)
    if choice != NEW_PATIENT:
        st.session_state.pid = choice
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


def baseline_on() -> bool:
    return st.session_state.get("baseline", True)


# ----------------------------------------------------------------------------- sidebar
def sidebar_footer() -> None:
    """Settings used by every page, at the bottom of the sidebar."""
    with st.sidebar:
        st.divider()
        st.checkbox("Add 48 baseline (1 month before the first change)", key="baseline",
                    help="Adds a raw point of 48/48 one month before the first dated box. Used by every page.")
        if st.button("Reload data"):
            load_tables.clear()
            st.rerun()
        st.caption(f"Data: {DATA_FILE.name}")
        if _on_streamlit_cloud():
            st.warning("Edits are saved on the app server only and are lost when the app restarts. "
                       "Download a backup after editing (All patients & data).")


def _on_streamlit_cloud() -> bool:
    return str(ROOT).startswith("/mount/src/")
