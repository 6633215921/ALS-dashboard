"""Changes to the tables. Each function takes the latest tables and returns new ones (or raises EditError).

The pages read the data once (cached) and build an edit from what the user typed; right before saving they reload
the data and apply the edit with these functions, so changes saved by someone else in the meantime are kept or
reported instead of being overwritten.
"""
from __future__ import annotations

import pandas as pd

from .model import COLUMNS, FORMS, TREATMENTS, TYPES, Tables, normalize, sorted_courses


class EditError(ValueError):
    """An edit that cannot be applied; the message is shown to the user."""


def upsert_patient(tables: Tables, old_id: str | None, form: dict, courses: list[dict]) -> Tables:
    """Add a patient (old_id None) or replace one patient's form row and all of their courses.

    A changed patient_id renames the patient: the row keeps its place and the courses move to the new ID.
    """
    forms = tables[FORMS]
    ids = set(forms["patient_id"])
    new_id = form["patient_id"]
    if old_id is not None and old_id not in ids:
        raise EditError(f"{old_id} is no longer in the data (deleted by someone else?). Press Reload data.")
    if new_id != old_id and new_id in ids:
        raise EditError(f"{new_id} already exists. Choose another patient ID.")
    pos = len(forms) if old_id is None else int((forms["patient_id"] == old_id).to_numpy().argmax())
    forms = pd.concat([forms.iloc[:pos], pd.DataFrame([form]), forms.iloc[pos + 1:]], ignore_index=True)
    others = tables[TREATMENTS][tables[TREATMENTS]["patient_id"] != old_id]
    mine = pd.DataFrame([{**c, "patient_id": new_id} for c in courses], columns=COLUMNS[TREATMENTS])
    return {**tables, FORMS: normalize(FORMS, forms),
            TREATMENTS: normalize(TREATMENTS, pd.concat([others, mine], ignore_index=True))}


def delete_patient(tables: Tables, pid: str) -> Tables:
    """Remove a patient's form row and all of their treatment courses."""
    return {**tables,
            FORMS: tables[FORMS][tables[FORMS]["patient_id"] != pid].reset_index(drop=True),
            TREATMENTS: tables[TREATMENTS][tables[TREATMENTS]["patient_id"] != pid].reset_index(drop=True)}


def update_types(tables: Tables, shown: pd.DataFrame, edited: pd.DataFrame, renames: dict[str, str]) -> Tables:
    """Save the treatment-type list. renames = {old name: new name}; renamed types are renamed in every course.

    shown = the list the user started from (to detect a change by someone else). A type still used in a course
    cannot be removed.
    """
    if not _same(TYPES, shown, tables[TYPES]):
        raise EditError("Someone else changed the treatment types. Press Reload data and redo your change.")
    new_types = normalize(TYPES, edited)
    removed = set(shown["treatment"]) - set(new_types["treatment"]) - set(renames)
    still_used = removed & set(tables[TREATMENTS]["treatment"])
    if still_used:
        raise EditError(f"Still used in treatment courses: {', '.join(sorted(still_used))}. "
                        "Change or delete those courses first.")
    treatments = tables[TREATMENTS].assign(treatment=tables[TREATMENTS]["treatment"].replace(renames))
    return {**tables, TYPES: new_types, TREATMENTS: treatments}


def replace_courses(tables: Tables, shown: pd.DataFrame, edited: pd.DataFrame, ids: list[str]) -> Tables:
    """Save the whole treatment-course table (shown = the rows the user started from)."""
    if not _same(TREATMENTS, sorted_courses(shown, ids), sorted_courses(tables[TREATMENTS], ids)):
        raise EditError("Someone else changed the treatment courses. Press Reload data and redo your change.")
    return {**tables, TREATMENTS: normalize(TREATMENTS, edited)}


def _same(name: str, a: pd.DataFrame, b: pd.DataFrame) -> bool:
    return normalize(name, a).equals(normalize(name, b))
