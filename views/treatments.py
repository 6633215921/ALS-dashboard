"""Treatments page: the list of treatment types and every treatment course in one table."""
from __future__ import annotations

import streamlit as st

from als import edits
from als.model import FORMS, TREATMENTS, TYPES, as_text, patient_ids, sorted_courses, treatment_names
from views import data, state
from views.widgets import course_columns


def render() -> None:
    st.title("Treatments")
    state.show_flash()
    tables = data.load_tables()
    _types_section(tables)
    _courses_section(tables)


def _types_section(tables) -> None:
    st.subheader("Treatment types")
    st.caption("The drugs the app offers. Add a row for a new drug and press Save types. Renaming a type renames "
               "it in every course. A type that is used in a course cannot be removed.")
    shown = tables[TYPES]
    key = f"types_{state.editor_version()}"
    edited = st.data_editor(shown, num_rows="dynamic", hide_index=True, key=key,
                            column_config={"treatment": st.column_config.TextColumn("Treatment", required=True),
                                           "notes": st.column_config.TextColumn("Notes")})
    if st.button("Save types", type="primary"):
        changes = st.session_state[key]              # the editor's own record of edited / added / deleted rows
        renames = {shown.iloc[int(row)]["treatment"]: as_text(change["treatment"])
                   for row, change in changes["edited_rows"].items() if "treatment" in change}
        try:
            after = edits.update_types(tables, edited, renames)
        except edits.EditError as err:
            st.error(str(err))
        else:
            data.save(tables, after, "Treatment types saved.")


def _courses_section(tables) -> None:
    st.subheader("All treatment courses")
    st.caption("One row per course: patient, treatment, start and stop (MM/YYYY, blank stop = still on). "
               "A patient can have several courses, also of the same drug. Same data as on the Patient form page.")
    ids = patient_ids(tables[FORMS])
    shown = sorted_courses(tables[TREATMENTS], ids)
    columns = {"patient_id": st.column_config.SelectboxColumn("Patient ID", options=ids, required=True),
               **course_columns(treatment_names(tables[TYPES]))}
    edited = st.data_editor(shown, num_rows="dynamic", hide_index=True, key=f"all_courses_{state.editor_version()}",
                            column_config=columns)
    if st.button("Save courses", type="primary"):
        data.save(tables, edits.replace_courses(tables, edited), "Treatment courses saved.")
