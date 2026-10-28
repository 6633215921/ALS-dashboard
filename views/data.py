"""The app's data file, data/raw_data.xlsx: first start, reading, noticing outside changes, saving.

Doctors can edit the data in the app or by opening data/raw_data.xlsx in Excel. To keep both safe:
  * The data is read again whenever the file changes (the cache is keyed by the file's version).
  * Every run checks whether the file changed outside this browser session (Excel, another window). If so, all
    editors start again from the new data and a save of an edit made on the old data is refused.
  * A file the app cannot use safely (a sheet or column missing, renamed or added) stops the pages with a list of
    what to fix, so the app never saves over data it did not read.
  * A save writes a complete new file and swaps it in (als.storage.save); if Excel has the file open, the save is
    refused with a message and the edit stays on the page.
"""
from __future__ import annotations

from pathlib import Path

import streamlit as st

from als import storage
from als.checks import error_keys, validate
from als.model import FORMS, Tables, empty_tables
from views import state

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "raw_data.xlsx"         # the live data; not in Git
SAMPLE_DIR = ROOT / "sample_data"
BLANK_FILE = SAMPLE_DIR / "raw_data_blank.xlsx"     # no patients, treatment types Riluzole and Edaravone
DUMMY_FILE = SAMPLE_DIR / "raw_data_DUMMY.xlsx"     # 22 DUMMY patients, for demos and training
KEEP = object()                                     # save(select=...) default: keep the selected patient


# ----------------------------------------------------------------------------- start of a run
def ensure_data_file() -> None:
    """First start: create the data file, blank on a computer, with the DUMMY patients on Streamlit Cloud."""
    if not DATA_FILE.exists():
        start = storage.load(DUMMY_FILE) if on_streamlit_cloud() and DUMMY_FILE.exists() else empty_tables()
        storage.save(DATA_FILE, start)


def sync() -> None:
    """Notice a change of the data file made outside this session. Call once per run, before any page."""
    version = storage.file_version(DATA_FILE)
    seen = st.session_state.get(state.SEEN_VERSION)
    changed = seen is not None and version != seen
    st.session_state[state.SEEN_VERSION] = version
    st.session_state[state.CHANGED_OUTSIDE] = changed
    if changed:
        state.reset_editors()
        st.info("The data file was changed outside this window (Excel or another window), so the page shows the "
                "latest data. If you were editing here, please make your change again.")


# ----------------------------------------------------------------------------- reading
@st.cache_data(max_entries=4, show_spinner="Loading data…")
def _read(path: str, version: tuple[int, int] | None) -> Tables:
    """The file's tables; `version` is only part of the cache key, so a changed file is read again."""
    return storage.load(Path(path))


def load_tables() -> Tables:
    """The data as it is in the file now. Stops the page with what to fix if the file cannot be used."""
    try:
        return _read(str(DATA_FILE), storage.file_version(DATA_FILE))
    except storage.WorkbookError as err:
        st.error(f"The data file cannot be used until it is fixed (in Excel): {DATA_FILE}\n\n"
                 + "\n".join(f"- {p}" for p in err.problems)
                 + f"\n\nThe app does not change the file meanwhile. To start again from an empty file, "
                   f"replace it with {BLANK_FILE.relative_to(ROOT)}.")
        st.stop()


def is_sample_data(tables: Tables) -> bool:
    """True if any patient's notes say DUMMY (the sample data)."""
    return bool(tables[FORMS]["notes"].str.contains("DUMMY", regex=False).any())


def on_streamlit_cloud() -> bool:
    return str(ROOT).startswith("/mount/src/")


# ----------------------------------------------------------------------------- saving
def save(before: Tables | None, after: Tables, message: str, select=KEEP, check: bool = True) -> None:
    """Write `after` and rerun the page with `message`; otherwise show why not and keep the edit on the page.

    before: the data the edit was applied to, to tell errors the edit adds from errors already in the data.
    select: the patient to select afterwards (None = no patient); leave out to keep the current one.
    check:  False saves even if the edit adds errors (upload, after the user has seen them).
    """
    if st.session_state.get(state.CHANGED_OUTSIDE):
        st.warning("Not saved: the data file was changed outside this window (Excel or another window) while you "
                   "were editing. The page now shows the latest data; please make your change again.")
        return
    if check:
        new_errors = error_keys(validate(after)) - error_keys(validate(before))
        if new_errors:
            st.error("Not saved. Please fix:\n" + "\n".join(f"- {pid}: {msg}" for pid, msg in sorted(new_errors)))
            return
    try:
        storage.save(DATA_FILE, after)
    except PermissionError:
        st.error(f"Not saved: {DATA_FILE.name} is open in another program (for example Excel). "
                 "Close it there and press the button again. Your changes are still on this page.")
        return
    except OSError as err:
        st.error(f"Not saved: could not write {DATA_FILE} ({err}). Your changes are still on this page.")
        return
    st.session_state[state.SEEN_VERSION] = storage.file_version(DATA_FILE)   # our own change, not an outside one
    state.flash(message)
    state.reset_editors()
    if select is not KEEP:
        state.select_patient(select)
    st.rerun()
