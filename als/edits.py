"""Changes to the tables. Each function takes the latest tables and returns new ones, or raises EditError.

The app applies an edit to the data as it is on disk right before saving (see views.data), so an edit only
changes the rows it is about.
"""
from __future__ import annotations

import pandas as pd

from .model import COLUMNS, FORMS, TREATMENTS, TYPES, Tables, normalize


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
        raise EditError(f"{old_id} is no longer in the data (deleted in Excel or another window?).")
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


def update_types(tables: Tables, edited: pd.DataFrame, renames: dict[str, str]) -> Tables:
    """Save the treatment-type list. renames = {old name: new name}; a renamed type is renamed in every course.

    A type that is still used in a course cannot be removed.
    """
    new_types = normalize(TYPES, edited)
    removed = set(tables[TYPES]["treatment"]) - set(new_types["treatment"]) - set(renames)
    still_used = removed & set(tables[TREATMENTS]["treatment"])
    if still_used:
        raise EditError(f"Still used in treatment courses: {', '.join(sorted(still_used))}. "
                        "Change or delete those courses first.")
    treatments = tables[TREATMENTS].assign(treatment=tables[TREATMENTS]["treatment"].replace(renames))
    return {**tables, TYPES: new_types, TREATMENTS: treatments}


def replace_courses(tables: Tables, edited: pd.DataFrame) -> Tables:
    """Save the whole treatment-course table."""
    return {**tables, TREATMENTS: normalize(TREATMENTS, edited)}
