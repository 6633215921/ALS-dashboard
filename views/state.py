"""What a browser session remembers between runs of a page (st.session_state), named in one place."""
from __future__ import annotations

import streamlit as st

PATIENT = "pid"                          # the selected patient, shared by every page
BASELINE = "baseline"                    # sidebar checkbox: add the 48 baseline point (key of that widget)
EDITORS = "ver"                          # part of every editor's key: a new value gives each editor fresh data
FLASH = "flash"                          # message shown once on the next run, e.g. "Saved MND-13."
SEEN_VERSION = "data_version"            # version of the data file this session saw last (views.data)
CHANGED_OUTSIDE = "changed_outside"      # True in a run in which the data file changed outside this session


def init() -> None:
    st.session_state.setdefault(BASELINE, True)


def baseline_on() -> bool:
    return st.session_state.get(BASELINE, True)


def selected_patient() -> str | None:
    return st.session_state.get(PATIENT)


def select_patient(pid: str | None) -> None:
    st.session_state[PATIENT] = pid


def editor_version() -> int:
    return st.session_state.get(EDITORS, 0)


def reset_editors() -> None:
    """Make every editor and patient picker start again from the data (their keys include the version)."""
    st.session_state[EDITORS] = editor_version() + 1


def flash(message: str) -> None:
    st.session_state[FLASH] = message


def show_flash() -> None:
    if message := st.session_state.pop(FLASH, None):
        st.success(message)
