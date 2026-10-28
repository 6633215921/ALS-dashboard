"""Patient form page: add, edit, rename or delete a patient (the paper form boxes + treatment courses)."""
from __future__ import annotations

import pandas as pd
import streamlit as st

from als import edits
from als.checks import validate
from als.codebook import CODEBOOK
from als.model import (
    BOX_PATTERN,
    COLUMNS,
    FORMS,
    ITEMS,
    LEVELS,
    TREATMENTS,
    TYPES,
    as_text,
    box,
    form_row,
    patient_ids,
    treatment_names,
)
from als.scoring import current_scores
from views import data, state
from views.widgets import NEW_PATIENT, course_columns, pick_patient

COURSE_COLS = ["treatment", "start", "stop", "notes"]
LEVEL_HELP = "Month the patient first reached this level: MM/YYYY, or YYYY if only the year is known, or ?"


def render() -> None:
    st.title("Patient form")
    state.show_flash()
    tables = data.load_tables()
    choice = pick_patient(patient_ids(tables[FORMS]), key="pick_form", allow_new=True, label="Patient")
    is_new = choice == NEW_PATIENT
    row = _blank_form() if is_new else form_row(tables, choice)
    treatments = tables[TREATMENTS]
    courses = treatments[treatments["patient_id"] == choice][COURSE_COLS].reset_index(drop=True)
    ver = state.editor_version()

    with st.form(f"patient_{choice}_{ver}"):
        c1, c2, c3 = st.columns(3)
        new_id = c1.text_input("Patient ID", row["patient_id"], placeholder="MND-26",
                               help="Study code only (MND-number). Never a name or hospital number.")
        language = c2.selectbox("Form language", ["TH", "EN"], index=1 if row["form_language"] == "EN" else 0)
        last = c3.text_input("Last assessed (MM/YYYY)", row["last_assessed"], placeholder="08/2026",
                             help="Month of the latest assessment. Needed when it is later than the last change.")
        notes = st.text_input("Notes", row["notes"])
        st.markdown("**ALSFRS-R**: month the patient first reached each level. Level 4 (normal) needs no "
                    "month. `2025` = only the year is known, `?` = reached by the latest month.(the patient has reached this level, but we don’t know the month)")
        boxes = st.data_editor(_box_grid(row), hide_index=True, disabled=["Item"], height=35 * 13 + 3,
                               column_config=_box_columns(), key=f"grid_{choice}_{ver}")
        st.markdown("**Treatment courses**: one row per course (add rows with +). Blank stop = still on. "
                    "A new drug must first be added on the Treatments page.")
        new_courses = st.data_editor(courses, num_rows="dynamic", hide_index=True, key=f"courses_{choice}_{ver}",
                                     column_config=course_columns(treatment_names(tables[TYPES])))
        submitted = st.form_submit_button("Add patient" if is_new else "Save changes", type="primary")

    if submitted:
        form = {"patient_id": as_text(new_id), "form_language": language, "last_assessed": as_text(last),
                "notes": as_text(notes),
                **{box(item, level): as_text(boxes.at[item, f"L{level}"]) for item in ITEMS for level in LEVELS}}
        course_rows = [{col: as_text(r[col]) for col in COURSE_COLS} for _, r in new_courses.iterrows()]
        _save_patient(tables, None if is_new else choice, form, course_rows)

    if not is_new:
        _saved_form_status(tables, choice, row)
    with st.expander("Level wording (paper form)"):
        st.dataframe(_wording(language))
    if not is_new:
        _delete_section(tables, choice, int((treatments["patient_id"] == choice).sum()), ver)


# ----------------------------------------------------------------------------- pieces
def _save_patient(tables, old_id: str | None, form: dict, courses: list[dict]) -> None:
    """Add (old_id None) or replace a patient, then save; an edit that cannot be applied shows why."""
    try:
        after = edits.upsert_patient(tables, old_id, form, courses)
    except edits.EditError as err:
        st.error(str(err))
        return
    action = "Added" if old_id is None else "Saved"
    data.save(tables, after, f"{action} {form['patient_id']}.", select=form["patient_id"])


def _blank_form() -> pd.Series:
    row = pd.Series({col: "" for col in COLUMNS[FORMS]})
    row["form_language"] = "TH"
    return row


def _box_grid(row: pd.Series) -> pd.DataFrame:
    """12 rows (items) x 4 columns (levels 3..0), indexed by item."""
    data = {"Item": [f"{c['no']}. {c['en']} · {c['th']}" for c in CODEBOOK.values()]}
    for level in LEVELS:
        data[f"L{level}"] = [row.get(box(item, level), "") for item in ITEMS]
    return pd.DataFrame(data, index=ITEMS)


def _box_columns() -> dict:
    levels = {f"L{level}": st.column_config.TextColumn(f"Level {level}", help=LEVEL_HELP, width="small",
                                                       validate=BOX_PATTERN) for level in LEVELS}
    return {"Item": st.column_config.TextColumn("Item", width="large"), **levels}


def _wording(language: str) -> pd.DataFrame:
    """Level wording of every item, as printed on the paper form."""
    k = 1 if language == "TH" else 0
    return pd.DataFrame({str(level): [c["levels"][level][k] for c in CODEBOOK.values()] for level in (4, 3, 2, 1, 0)},
                        index=[f"{c['no']}. {c['en']}" for c in CODEBOOK.values()])


def _saved_form_status(tables, pid: str, row: pd.Series) -> None:
    scores = current_scores(row)
    st.caption(f"Saved form: ALSFRS-R {scores['als_score']}/48 · bulbar {scores['bulbar']} · fine motor "
               f"{scores['fine_motor']} · gross motor {scores['gross_motor']} · respiratory {scores['respiratory']}")
    messages = [f"{i.level}: {i.message}" for i in validate(tables) if i.patient_id == pid]
    if messages:
        st.warning("Checks for this patient:\n" + "\n".join(f"- {m}" for m in messages))


def _delete_section(tables, pid: str, n_courses: int, ver: int) -> None:
    with st.expander("Delete this patient"):
        st.write(f"Deletes the form of **{pid}** and its {n_courses} treatment course(s). This cannot be undone; "
                 "download a copy first if unsure (All patients & data).")
        confirmed = st.checkbox(f"Yes, delete {pid}", key=f"del_{pid}_{ver}")
        if st.button("Delete patient", disabled=not confirmed, type="primary"):
            data.save(tables, edits.delete_patient(tables, pid), f"Deleted {pid}.", select=None)
