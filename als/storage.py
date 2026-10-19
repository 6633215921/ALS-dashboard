"""Where the data lives: the Excel workbook data/raw_data.xlsx.

It holds the three tables of als.model (forms, treatments, treatment_types) as text, e.g. "03/2026".
"""
from __future__ import annotations

import io
import os
import tempfile
from pathlib import Path

import pandas as pd
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill

from .model import COLUMNS, Tables, empty_tables, normalize

README_LINES = [
    "ALS progress data (ALSFRS-R). Edit in the web app; this file is the data store / backup.",
    "",
    "forms: one row per patient. patient_id = study code only (MND-13), never a name or HN.",
    "  q{n}_{item}_L3 / L2 / L1 / L0 = month (MM/YYYY, AD) the patient first reached that level.",
    "  Leave level 4 (normal) out. YYYY alone = month unknown (counted as July). ? = reached by the latest month.",
    "  last_assessed = month of the latest assessment (MM/YYYY), if later than the last change.",
    "treatments: one row per treatment course: patient_id, treatment, start, stop (MM/YYYY; blank stop = still on).",
    "  A patient can have any number of courses, also of the same drug (stopped and restarted).",
    "treatment_types: the treatments the app offers. Add a row to add a new drug.",
    "",
    "Keep every cell as text (Format Cells > Text in Excel) so 03/2026 does not turn into a date.",
    "Scores, slopes and the monthly timeline are calculated by the app (All patients & data > download).",
]
HEADER_FONT = Font(name="Arial", size=10, bold=True)
HEADER_FILL = PatternFill("solid", fgColor="FFD9E2F3")


# ----------------------------------------------------------------------------- workbook <-> tables
def to_workbook_bytes(tables: Tables, results: dict[str, pd.DataFrame] | None = None) -> bytes:
    """xlsx: README, the three data tables (as text), then optional result sheets (e.g. summary, timeline)."""
    wb = Workbook()
    readme = wb.active
    readme.title = "README"
    for i, line in enumerate(README_LINES, 1):
        readme.cell(i, 1, line).font = Font(name="Arial", size=10, bold=i == 1)
    readme.column_dimensions["A"].width = 120
    for name in COLUMNS:
        _write_sheet(wb, name, normalize(name, tables.get(name)), as_text=True)
    for name, df in (results or {}).items():
        _write_sheet(wb, name, df, as_text=False)
    out = io.BytesIO()
    wb.save(out)
    return out.getvalue()


def _write_sheet(wb: Workbook, name: str, df: pd.DataFrame, as_text: bool) -> None:
    ws = wb.create_sheet(name)
    for j, col in enumerate(df.columns, 1):
        cell = ws.cell(1, j, col)
        cell.font, cell.fill = HEADER_FONT, HEADER_FILL
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        ws.column_dimensions[cell.column_letter].width = max(10, min(40, len(str(col)) + 2))
    for i, row in enumerate(df.itertuples(index=False), 2):
        for j, value in enumerate(row, 1):
            if value is None or (not isinstance(value, str) and pd.isna(value)):
                continue
            cell = ws.cell(i, j, str(value) if as_text else value)
            if as_text:
                cell.number_format = "@"                    # keep 03/2026 as text in Excel
            elif isinstance(value, pd.Timestamp):
                cell.number_format = "mm/yyyy"
    ws.freeze_panes = "B2"
    ws.row_dimensions[1].height = 30


def read_workbook(source) -> Tables:
    """Tables from an xlsx path or uploaded file. A missing sheet gives an empty table (default treatment types)."""
    wb = load_workbook(source, read_only=True, data_only=True)
    tables = empty_tables()
    for name in COLUMNS:
        if name not in wb.sheetnames:
            continue
        rows = list(wb[name].iter_rows(values_only=True))
        if not rows:
            continue
        header = [str(h).strip() if h is not None else "" for h in rows[0]]
        df = pd.DataFrame([list(r) + [None] * (len(header) - len(r)) for r in rows[1:]], columns=header)
        df = df.loc[:, [h for h in header if h]]
        tables[name] = normalize(name, df.map(_date_to_month))
    wb.close()
    return tables


def _date_to_month(value):
    """If Excel turned 03/2026 into a date, turn it back into MM/YYYY."""
    return value.strftime("%m/%Y") if hasattr(value, "strftime") else value


# ----------------------------------------------------------------------------- the data file
def load(path: Path) -> Tables:
    """The tables in the workbook (empty tables if the file does not exist yet)."""
    return read_workbook(path) if Path(path).exists() else empty_tables()


def save(path: Path, tables: Tables) -> None:
    """Rewrite the workbook, all or nothing: write a temporary file, then replace the old one."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".xlsx")
    with os.fdopen(fd, "wb") as fh:
        fh.write(to_workbook_bytes(tables))
    os.replace(tmp, path)
