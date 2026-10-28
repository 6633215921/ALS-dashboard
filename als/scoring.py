"""ALSFRS-R calculations for one patient: item scores, raw points, monthly timeline, treatment states, slopes.

  * item score in month m = the lowest level whose month is <= m (4 if none);
    'YYYY' = July of that year, '?' = reached by the patient's latest month
  * raw points = months with a level change, + optional 48 baseline one month before the first change,
    + last_assessed if it is later than the last change
  * monthly timeline between the first and last raw point: Linear (base for slopes) / Step / raw points only
  * treatment in month m = every drug whose course covers m (the stop month counts as on), joined with ' + '
  * slope = least-squares line through the monthly sum_score, in ALSFRS-R points per month
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import NamedTuple

import numpy as np
import pandas as pd

from .model import (
    BEFORE,
    BOX_COLS,
    DOMAINS,
    ITEMS,
    LEVELS,
    NO_DRUG,
    NONE_RECORDED,
    OFF,
    TREATMENTS,
    TYPES,
    Tables,
    as_text,
    box,
    form_row,
    is_month,
    parse_month,
    treatment_names,
)

LINEAR, STEP, RAW_ONLY = "linear", "step", "none"
POINT_COLS = ["month_no", *ITEMS, "sum_score", "point_type"]
GRID_COLS = ["month_no", *ITEMS, "sum_score", "source", "point_type", "treatment", "on_treatment"]


@dataclass(frozen=True)
class Course:
    treatment: str
    start: int                      # month number
    stop: int | None                # None = still on


class Fit(NamedTuple):
    slope: float                    # ALSFRS-R points per month
    intercept: float                # score at month number 0, so score = intercept + slope * month_no
    n: int                          # points used


# ----------------------------------------------------------------------------- form -> scores
def effective_months(row: pd.Series) -> dict[str, int]:
    """{box column: month number} for every filled box; '?' becomes the patient's latest month."""
    parsed = {col: parse_month(row.get(col, "")) for col in BOX_COLS}
    latest = max((m for m in parsed.values() if m is not None), default=None)
    months = {}
    for col, m in parsed.items():
        if m is not None:
            months[col] = m
        elif as_text(row.get(col, "")) == "?" and latest is not None:
            months[col] = latest
    return months


def item_levels_at(months: dict[str, int], m: int) -> list[int]:
    """Score of each of the 12 items in month m."""
    scores = []
    for item in ITEMS:
        score = 4
        for level in LEVELS:                        # 3, 2, 1, 0: the lowest level reached wins
            reached = months.get(box(item, level))
            if reached is not None and reached <= m:
                score = level
        scores.append(score)
    return scores


def current_scores(row: pd.Series) -> dict[str, int]:
    """Item, domain and total scores as on the form today (lowest level with any entry, else 4)."""
    scores = {}
    for item in ITEMS:
        filled = [level for level in LEVELS if as_text(row.get(box(item, level), ""))]
        scores[item] = min(filled, default=4)
    for domain, items in DOMAINS.items():
        scores[domain] = sum(scores[i] for i in items)
    scores["als_score"] = sum(scores[i] for i in ITEMS)
    return scores


def raw_points(row: pd.Series, baseline: bool = True) -> pd.DataFrame:
    """One row per raw point: month_no, the 12 item scores, sum_score, point_type."""
    months = effective_months(row)
    changes = sorted(set(months.values()))
    if not changes:
        return pd.DataFrame(columns=POINT_COLS)
    points = [(changes[0] - 1, "baseline")] if baseline else []
    points += [(m, "change") for m in changes]
    last = parse_month(row.get("last_assessed", ""))
    if last is not None and last > changes[-1]:
        points.append((last, "last assessment"))
    rows = []
    for m, kind in points:
        levels = [4] * len(ITEMS) if kind == "baseline" else item_levels_at(months, m)
        rows.append([m, *levels, sum(levels), kind])
    return pd.DataFrame(rows, columns=POINT_COLS)


# ----------------------------------------------------------------------------- treatments
def patient_courses(treatments: pd.DataFrame, pid: str) -> list[Course]:
    """The patient's courses with a valid start month (others are reported by checks.validate)."""
    courses = []
    for r in treatments[treatments["patient_id"] == pid].itertuples():
        name, start, stop = as_text(r.treatment), as_text(r.start), as_text(r.stop)
        if name and is_month(start):
            courses.append(Course(name, parse_month(start), parse_month(stop) if is_month(stop) else None))
    return courses


def treatment_label(m: int, courses: list[Course], order: list[str]) -> str:
    """'Riluzole', 'Riluzole + Edaravone', 'before treatment', 'off treatment' or 'no treatment recorded'."""
    if not courses:
        return NONE_RECORDED
    active = {c.treatment for c in courses if c.start <= m and (c.stop is None or m <= c.stop)}
    if active:
        rank = {name: i for i, name in enumerate(order)}
        return " + ".join(sorted(active, key=lambda name: (rank.get(name, len(rank)), name)))
    return BEFORE if m < min(c.start for c in courses) else OFF


# ----------------------------------------------------------------------------- monthly timeline
def monthly(points: pd.DataFrame, courses: list[Course], order: list[str], method: str = LINEAR) -> pd.DataFrame:
    """Raw points plus every month in between (LINEAR or STEP); RAW_ONLY keeps the raw points only."""
    if points.empty:
        return pd.DataFrame(columns=GRID_COLS)
    points = points.sort_values("month_no").reset_index(drop=True)
    xs = points["month_no"].to_numpy(float)
    months = (points["month_no"].to_numpy(int) if method == RAW_ONLY
              else np.arange(int(xs.min()), int(xs.max()) + 1))
    grid = pd.DataFrame({"month_no": months})
    for col in [*ITEMS, "sum_score"]:
        ys = points[col].to_numpy(float)
        if method == STEP:                          # hold the last raw value
            grid[col] = ys[np.clip(np.searchsorted(xs, months, side="right") - 1, 0, len(ys) - 1)]
        else:
            grid[col] = np.interp(months.astype(float), xs, ys)
    kinds = dict(zip(points["month_no"].astype(int), points["point_type"], strict=True))
    grid["source"] = ["raw" if m in kinds else "interpolated" for m in months]
    grid["point_type"] = [kinds.get(m, "interpolated") for m in months]
    grid["treatment"] = [treatment_label(int(m), courses, order) for m in months]
    grid["on_treatment"] = (~grid["treatment"].isin(NO_DRUG)).astype(int)
    return grid[GRID_COLS]


def patient_timeline(tables: Tables, pid: str, baseline: bool = True, method: str = LINEAR):
    """(raw points, courses, monthly timeline) of one patient."""
    points = raw_points(form_row(tables, pid), baseline)
    courses = patient_courses(tables[TREATMENTS], pid)
    return points, courses, monthly(points, courses, treatment_names(tables[TYPES]), method)


# ----------------------------------------------------------------------------- slopes
def fit(points: pd.DataFrame) -> Fit | None:
    """Least-squares line of sum_score on month_no; None if fewer than 2 distinct months."""
    if len(points) < 2 or points["month_no"].nunique() < 2:
        return None
    x = points["month_no"].to_numpy(float)
    slope, intercept = np.polyfit(x - x.min(), points["sum_score"].to_numpy(float), 1)
    return Fit(float(slope), float(intercept - slope * x.min()), len(points))


def slope_groups(grid: pd.DataFrame, months: tuple[int, int] | None = None) -> dict[str, pd.DataFrame]:
    """Months used by each slope: all, before (first drug), on (any drug), and range (time of interest)."""
    groups = {"all": grid,
              "before": grid[grid["treatment"] == BEFORE],
              "on": grid[grid["on_treatment"] == 1]}
    if months is not None:
        groups["range"] = grid[grid["month_no"].between(*months)]
    return groups


def round_slope(slope: float) -> float:
    """Slope to 2 decimals for display (+ 0.0 turns -0.0 into 0.0, so it never shows as '-0.00')."""
    return round(slope, 2) + 0.0


def rounded(result: Fit | None) -> float | None:
    """The fit's slope for display, None without a fit."""
    return None if result is None else round_slope(result.slope)
