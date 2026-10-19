"""Data checks. Errors = data the app cannot read correctly; warnings = data that reads fine but looks unusual."""
from __future__ import annotations

import re
from typing import NamedTuple

from .model import (
    BOX_COLS,
    BOX_PATTERN,
    FORMS,
    ITEMS,
    LEVELS,
    NO_DRUG,
    OPTIONAL_MONTH_PATTERN,
    PATIENT_ID,
    TREATMENTS,
    TYPES,
    Tables,
    box,
    is_month,
    parse_month,
    treatment_names,
)
from .scoring import effective_months, monthly, patient_courses, raw_points

ERROR, WARNING = "error", "warning"
ANY_PATIENT = "*"                                   # issue not tied to one patient


class Issue(NamedTuple):
    patient_id: str
    level: str                                      # ERROR or WARNING
    message: str


def validate(tables: Tables) -> list[Issue]:
    forms, treatments, types = tables[FORMS], tables[TREATMENTS], tables[TYPES]
    issues: list[Issue] = []

    def error(pid, message):
        issues.append(Issue(pid or ANY_PATIENT, ERROR, message))

    def warning(pid, message):
        issues.append(Issue(pid or ANY_PATIENT, WARNING, message))

    # patient IDs
    ids = forms["patient_id"].tolist()
    for pid in ids:
        if not pid:
            error(ANY_PATIENT, "a patient row has no patient_id")
        elif not PATIENT_ID.match(pid):
            error(pid, "patient_id: use a study code like MND-13 (letters, digits, - or _ only)")
    for pid in sorted({p for p in ids if p and ids.count(p) > 1}):
        error(pid, "duplicate patient_id")

    # the form boxes
    for _, row in forms.iterrows():
        pid = row["patient_id"]
        bad = [col for col in BOX_COLS if not re.match(BOX_PATTERN, row[col])]
        if bad:
            error(pid, f"{len(bad)} box(es) not MM/YYYY, YYYY or ? ({', '.join(bad[:2])})")
        if not re.match(OPTIONAL_MONTH_PATTERN, row["last_assessed"]):
            error(pid, "last_assessed not MM/YYYY")
        for item in ITEMS:
            dated = [parse_month(row[box(item, lv)]) for lv in LEVELS if is_month(row[box(item, lv)])]
            if dated != sorted(dated):
                warning(pid, f"{item}: a worse level has an earlier month than a milder one")
        months = effective_months(row)
        last = parse_month(row["last_assessed"])
        if months and last is not None and last < max(months.values()):
            warning(pid, "last_assessed is before the last month on the form")

    # treatment courses and types
    known = treatment_names(types)
    for _, r in treatments.iterrows():
        pid, name = r["patient_id"], r["treatment"] or "treatment"
        if not pid:
            error(ANY_PATIENT, f"a {name} row has no patient_id")
        elif pid not in ids:
            error(pid, f"{name}: patient {pid} is not in forms")
        if r["treatment"] not in known:
            error(pid, f"unknown treatment '{r['treatment']}' (add it under Treatment types)")
        if not is_month(r["start"]):
            error(pid, f"{name}: start not MM/YYYY")
        if r["stop"] and not is_month(r["stop"]):
            error(pid, f"{name}: stop not MM/YYYY")
        start, stop = parse_month(r["start"]), parse_month(r["stop"])
        if start is not None and stop is not None and stop < start:
            error(pid, f"{name}: stop is before start")
    for name in known:
        if "+" in name or name in NO_DRUG:
            error(ANY_PATIENT, f"treatment type '{name}': do not use '+' or the words {sorted(NO_DRUG)}")
    if len(set(known)) != len(known):
        error(ANY_PATIENT, "a treatment type is listed twice")

    # enough data on treatment for a slope
    for pid in dict.fromkeys(p for p in ids if p):
        points = raw_points(forms[forms["patient_id"] == pid].iloc[0])
        grid = monthly(points, patient_courses(treatments, pid), known)
        on = grid["on_treatment"] == 1
        if on.any() and (on & (grid["source"] == "raw")).sum() < 3:
            warning(pid, "fewer than 3 raw points on treatment")
    return issues


def error_keys(issues: list[Issue]) -> set[tuple[str, str]]:
    """(patient, message) of every error, to compare the data before and after an edit."""
    return {(i.patient_id, i.message) for i in issues if i.level == ERROR}


def by_patient(issues: list[Issue]) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    for issue in issues:
        out.setdefault(issue.patient_id, []).append(issue.message)
    return out
