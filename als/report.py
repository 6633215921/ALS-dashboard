"""Results for all patients: the summary table and the monthly score timeline."""
from __future__ import annotations

import pandas as pd

from .checks import by_patient, validate
from .model import BEFORE, DOMAINS, FORMS, Tables, format_month, month_start, natural_key
from .scoring import GRID_COLS, LINEAR, current_scores, fit, patient_timeline, rounded, slope_groups

TIMELINE_COLS = ["id", "date", *GRID_COLS]


def timeline(tables: Tables, baseline: bool = True, method: str = LINEAR) -> pd.DataFrame:
    """One row per patient per month (or per raw point with RAW_ONLY)."""
    parts = []
    for pid in tables[FORMS]["patient_id"]:
        if not pid:
            continue
        _, _, grid = patient_timeline(tables, pid, baseline, method)
        if not grid.empty:
            parts.append(grid.assign(id=pid, date=grid["month_no"].map(month_start)))
    return pd.concat(parts, ignore_index=True)[TIMELINE_COLS] if parts else pd.DataFrame(columns=TIMELINE_COLS)


def summary(tables: Tables, baseline: bool = True, method: str = LINEAR) -> pd.DataFrame:
    """One row per patient (natural ID order): current domain scores, treatments, raw-point counts, slopes, checks."""
    issues = by_patient(validate(tables))
    forms = tables[FORMS]
    order = sorted(range(len(forms)), key=lambda i: natural_key(forms["patient_id"].iat[i]))
    rows = []
    for _, form in forms.iloc[order].iterrows():
        pid = form["patient_id"]
        if not pid:
            continue
        scores = current_scores(form)
        _, courses, grid = patient_timeline(tables, pid, baseline, method)
        groups = slope_groups(grid)
        raw = grid[grid["source"] == "raw"]
        rows.append({
            "patient_id": pid,
            **{domain: scores[domain] for domain in DOMAINS},
            "als_score": scores["als_score"],
            "first_treatment": format_month(min((c.start for c in courses), default=None)),
            "treatments": ", ".join(dict.fromkeys(c.treatment for c in courses)),
            "n_raw_points": len(raw),
            "slope_all": rounded(fit(groups["all"])),
            "n_raw_before": int((raw["treatment"] == BEFORE).sum()),
            "slope_before": rounded(fit(groups["before"])),
            "n_raw_on_treatment": int((raw["on_treatment"] == 1).sum()),
            "slope_on_treatment": rounded(fit(groups["on"])),
            "check": "; ".join(issues.get(pid, [])),
        })
    return pd.DataFrame(rows)

