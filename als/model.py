"""The three data tables, their columns, and month handling.

Every stored value is text:
  forms            one row per patient: patient_id, form_language, last_assessed, notes,
                   + 48 boxes q{n}_{Item}_L3/L2/L1/L0 = month (MM/YYYY) the patient first reached that level
  treatments       one row per treatment course: patient_id, treatment, start, stop (MM/YYYY), notes
  treatment_types  the treatments the app offers: treatment, notes
Months are handled as month numbers (year * 12 + month) so that differences are in months.
"""
from __future__ import annotations

import re

import pandas as pd

from .codebook import CODEBOOK

Tables = dict[str, pd.DataFrame]

# ----------------------------------------------------------------------------- ALSFRS-R form
ITEMS = list(CODEBOOK)                              # q1_Speech ... q12_Respiratory_Insufficiency
LEVELS = (3, 2, 1, 0)                               # level 4 = normal, never dated
DOMAINS = {"bulbar": ITEMS[0:3], "fine_motor": ITEMS[3:6],
           "gross_motor": ITEMS[6:9], "respiratory": ITEMS[9:12]}


def box(item: str, level: int) -> str:
    """Column name of one box on the form, e.g. q1_Speech_L3."""
    return f"{item}_L{level}"


BOX_COLS = [box(item, level) for item in ITEMS for level in LEVELS]

# ----------------------------------------------------------------------------- tables
FORMS, TREATMENTS, TYPES = "forms", "treatments", "treatment_types"
COLUMNS = {
    FORMS: ["patient_id", "form_language", "last_assessed", "notes", *BOX_COLS],
    TREATMENTS: ["patient_id", "treatment", "start", "stop", "notes"],
    TYPES: ["treatment", "notes"],
}
DEFAULT_TYPES = ("Riluzole", "Edaravone")

# Treatment states that are not a drug.
BEFORE, OFF, NONE_RECORDED = "before treatment", "off treatment", "no treatment recorded"
NO_DRUG = {BEFORE, OFF, NONE_RECORDED}

# Input rules. The *_PATTERN strings are also checked in the browser (data editor), so keep them JavaScript-safe.
PATIENT_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_-]{1,19}$")
MONTH = re.compile(r"^(0[1-9]|1[0-2])/(\d{4})$")                      # MM/YYYY
BOX_PATTERN = r"^$|^\?$|^(19|20)\d{2}$|^(0[1-9]|1[0-2])/(19|20)\d{2}$"  # blank, ?, YYYY or MM/YYYY
OPTIONAL_MONTH_PATTERN = r"^$|^(0[1-9]|1[0-2])/(19|20)\d{2}$"          # blank or MM/YYYY


def as_text(value) -> str:
    """Cell value as stripped text: None / NaN -> '', 2025.0 -> '2025'."""
    if value is None or (not isinstance(value, str) and pd.isna(value)):
        return ""
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()


def empty_tables() -> Tables:
    tables = {name: pd.DataFrame(columns=cols) for name, cols in COLUMNS.items()}
    tables[TYPES] = pd.DataFrame({"treatment": list(DEFAULT_TYPES), "notes": [""] * len(DEFAULT_TYPES)})
    return tables


def normalize(name: str, df: pd.DataFrame | None) -> pd.DataFrame:
    """The table's columns in order, every value as text, fully blank rows dropped."""
    cols = COLUMNS[name]
    df = pd.DataFrame(columns=cols) if df is None else df.copy()
    for col in cols:
        if col not in df.columns:
            df[col] = ""
    df = df[cols].astype(object).map(as_text)
    return df[(df != "").any(axis=1)].reset_index(drop=True)


# ----------------------------------------------------------------------------- months
def is_month(text: str) -> bool:
    """True for a strict MM/YYYY."""
    return bool(MONTH.match(text))


def parse_month(text) -> int | None:
    """'03/2026' -> month number; '2025' -> July 2025 (year only); anything else -> None."""
    text = as_text(text)
    m = re.fullmatch(r"(\d{1,2})/(\d{4})", text)
    if m and 1 <= int(m.group(1)) <= 12:
        return int(m.group(2)) * 12 + int(m.group(1))
    if re.fullmatch(r"\d{4}", text):
        return int(text) * 12 + 7
    return None


def format_month(m) -> str:
    """Month number -> 'MM/YYYY' ('' for none)."""
    return "" if m is None or pd.isna(m) else f"{(int(m) - 1) % 12 + 1:02d}/{(int(m) - 1) // 12}"


def month_start(m) -> pd.Timestamp:
    """Month number -> first day of that month."""
    m = int(m)
    return pd.Timestamp(year=(m - 1) // 12, month=(m - 1) % 12 + 1, day=1)


# ----------------------------------------------------------------------------- lookups
def form_row(tables: Tables, pid: str) -> pd.Series:
    """The patient's row in forms."""
    forms = tables[FORMS]
    return forms[forms["patient_id"] == pid].iloc[0]


def natural_key(pid: str) -> tuple[int, str]:
    """Sort key that puts MND-2 before MND-10."""
    digits = re.findall(r"\d+", pid)
    return (int(digits[0]) if digits else 10**9, pid)


def patient_ids(forms: pd.DataFrame) -> list[str]:
    """Patient IDs in natural order."""
    return sorted((p for p in forms["patient_id"] if p), key=natural_key)


def treatment_names(types: pd.DataFrame) -> list[str]:
    """Treatment types in the order they are listed (used for colours and 'A + B' labels)."""
    return [t for t in types["treatment"] if t]


def sorted_courses(treatments: pd.DataFrame, ids: list[str]) -> pd.DataFrame:
    """Treatment courses ordered by patient (as in ids), start month, treatment."""
    if treatments.empty:
        return treatments
    rank = {pid: i for i, pid in enumerate(ids)}
    keys = [(rank.get(r.patient_id, 10**9), parse_month(r.start) or 0, r.treatment)
            for r in treatments.itertuples()]
    order = sorted(range(len(keys)), key=keys.__getitem__)
    return treatments.iloc[order].reset_index(drop=True)
