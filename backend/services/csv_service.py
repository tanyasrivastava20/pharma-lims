"""CSV export and import.

Export: files open cleanly in Excel (UTF-8 with BOM) and are protected against CSV injection
(a cell starting with = + - @ would run as a formula in Excel, so it is prefixed with an apostrophe).

Import: the whole file is checked first. If any row has a problem NOTHING is imported and every
problem is reported with its row number. A blank cell means "leave unchanged" (or the default)."""
import csv
import io
from datetime import date, datetime

from flask import Response, request

from database import db
from utils.responses import APIError
from utils.logging_setup import audit

MAX_ROWS = 2000
MAX_EXPORT_ROWS = 50000
_DANGEROUS = ("=", "+", "-", "@", "\t", "\r")
_BOOL_WORDS = {"yes": True, "true": True, "1": True, "no": False, "false": False, "0": False}


# ------------------------------------------------------------------ export
def _cell(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, datetime):
        return value.isoformat(timespec="seconds")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, float):
        return f"{value:.6f}".rstrip("0").rstrip(".")
    text = str(value)
    return "'" + text if text.startswith(_DANGEROUS) else text


def csv_response(rows, columns, name):
    """rows: list of dicts. columns: the keys to write, in order."""
    out = io.StringIO(newline="")
    writer = csv.writer(out)
    writer.writerow(columns)
    for row in rows:
        writer.writerow([_cell(row.get(c)) for c in columns])
    response = Response(("\ufeff" + out.getvalue()).encode("utf-8"))
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = f'attachment; filename="{name}_{datetime.now():%Y%m%d_%H%M%S}.csv"'
    return response


# ------------------------------------------------------------------ import
def read_upload(required, allowed):
    """Returns ([(line_number, {column: text}), ...], [ignored column names])."""
    upload = request.files.get("file")
    raw = upload.read() if upload else request.get_data()
    if not raw:
        raise APIError("No CSV data received. Send a file field named 'file', or the CSV text as the request body", 400)
    try:
        text = raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        raise APIError("The file must be UTF-8 text (in Excel: Save As > CSV UTF-8)", 400)
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise APIError("The file is empty", 400)
    reader.fieldnames = [(h or "").strip().lower() for h in reader.fieldnames]
    missing = [c for c in required if c not in reader.fieldnames]
    if missing:
        raise APIError("Missing required column(s): " + ", ".join(missing), 400)
    ignored = [h for h in reader.fieldnames if h and h not in allowed]
    rows = []
    for raw_row in reader:
        line = reader.line_num
        if None in raw_row:
            raise APIError(f"Row {line} has more values than the header has columns", 400)
        if not any((v or "").strip() for v in raw_row.values()):
            continue  # skip blank lines
        rows.append((line, {k: v for k, v in raw_row.items() if k in allowed}))
        if len(rows) > MAX_ROWS:
            raise APIError(f"Too many rows (limit {MAX_ROWS} per file)", 400)
    if not rows:
        raise APIError("The file has a header but no data rows", 400)
    return rows, ignored


def _clean(raw, bool_cols):
    out = {}
    for key, value in raw.items():
        value = (value or "").strip()
        if len(value) > 1 and value[0] == "'" and value[1] in "=+-@":
            value = value[1:]  # undo the export's injection protection
        if value == "":
            continue
        if key in bool_cols and value.lower() in _BOOL_WORDS:
            value = _BOOL_WORDS[value.lower()]
        out[key] = value
    return out


def run_import(rows, key_col, find_existing, validate, build, apply_update, mode, dry_run, bool_cols=(), label=None):
    """Checks every row, then (unless dry_run) saves them all in one go."""
    problems, plan, seen = [], [], {}
    for line, raw in rows:
        data = _clean(raw, bool_cols)
        key = str(data.get(key_col, "")).upper()
        row_errors = {}
        if key and key in seen:
            row_errors[key_col] = f"Duplicate of row {seen[key]} in this file"
        existing = find_existing(key) if key else None
        if existing is not None and mode == "create":
            row_errors[key_col] = "Already exists (use mode=upsert to update existing records)"
        if not row_errors:
            try:
                values = validate(data, existing)
            except APIError as e:
                row_errors = e.errors or {"row": e.message}
        if key:
            seen.setdefault(key, line)
        if row_errors:
            problems.append({"row": line, key_col: key or None, "errors": row_errors})
        else:
            plan.append((existing, values))
    if problems:
        raise APIError(f"{len(problems)} of {len(rows)} row(s) have problems. Nothing was imported", 400, problems)
    created = sum(1 for existing, _ in plan if existing is None)
    result = {"dry_run": dry_run, "mode": mode, "rows": len(plan), "to_create": created, "to_update": len(plan) - created}
    if dry_run:
        return result
    for existing, values in plan:
        if existing is None:
            db.session.add(build(values))
        else:
            apply_update(existing, values)
    db.session.commit()
    audit.info("CSV import (%s): created=%s updated=%s mode=%s", label or key_col, created, len(plan) - created, mode)
    return result
