"""Master data: parties, test characteristics, miscellaneous, assays, sampling inspection, specifications.
All six share one set of rules. Public field names match the frontend (type, group, limit, material);
the database columns are named differently where the frontend's names are SQL reserved words."""
import re

from flask import request

from database import db
from models import (Assay, Miscellaneous, Party, Product, Sample, SamplingInspection, Specification,
                    TestCharacteristic)
from models.constants import TEST_TYPES
from utils.query import apply_sort, like_pattern
from utils.responses import APIError
from utils.validation import clean_text
from utils.logging_setup import audit

CODE_RE = re.compile(r"^[A-Z0-9][A-Z0-9._-]{0,29}$")

# public field -> (database column, max length)
MASTERS = {
    "party": dict(model=Party, label="Party", fields={"city": ("city", 80)}),
    "test": dict(model=TestCharacteristic, label="Test characteristic",
                 fields={"type": ("test_type", 30), "unit": ("unit", 20)}),
    "misc": dict(model=Miscellaneous, label="Miscellaneous entry", fields={"group": ("group_name", 40)}),
    "assay": dict(model=Assay, label="Assay", fields={"method": ("method", 60), "limit": ("limit_range", 60)}),
    "sampling": dict(model=SamplingInspection, label="Sampling plan", fields={"plan": ("plan", 60), "level": ("level", 20)}),
    "spec": dict(model=Specification, label="Specification",
                 fields={"material": ("material_code", 30), "version": ("version", 20)}),
}
ALIASES = {"parties": "party", "tests": "test", "test-characteristics": "test", "test_characteristics": "test",
           "miscellaneous": "misc", "assays": "assay", "sampling-inspection": "sampling",
           "sampling_inspection": "sampling", "specifications": "spec", "specification": "spec"}


def resolve(kind):
    key = ALIASES.get(kind.lower(), kind.lower())
    if key not in MASTERS:
        raise APIError(f"Unknown master type '{kind}'. Valid types: {', '.join(MASTERS)}", 404)
    return key, MASTERS[key]


def to_api(row, cfg):
    d = row.to_dict()
    out = {"id": d["id"], "code": d["code"], "name": d["name"]}
    for api, (col, _) in cfg["fields"].items():
        out[api] = d[col]
    out["created_at"], out["updated_at"] = d["created_at"], d["updated_at"]
    return out


def validate(key, cfg, data, creating, row=None):
    errors, values = {}, {}
    if creating:
        code = (clean_text(data, "code", 30, errors, True) or "").upper()
        if code and "code" not in errors and not CODE_RE.match(code):
            errors["code"] = "Letters, numbers, dot, dash or underscore only"
        values["code"] = code
    elif "code" in data and str(data["code"]).strip().upper() != row.code:
        errors["code"] = "Code cannot be changed"
    if creating or "name" in data:
        name = clean_text(data, "name", 150, errors, True)
        if "name" not in errors:
            values["name"] = name
    for api, (col, max_len) in cfg["fields"].items():
        if api in data:
            value = clean_text(data, api, max_len, errors)
            if api not in errors:
                values[col] = value
    if values.get("test_type") and values["test_type"] not in TEST_TYPES:
        errors["type"] = "Must be one of: " + ", ".join(TEST_TYPES)
    if values.get("material_code"):
        values["material_code"] = values["material_code"].upper()
        if not Product.query.filter_by(material_code=values["material_code"]).first():
            errors["material"] = "Unknown material code"
    if errors:
        raise APIError("Validation failed", 400, errors)
    return values


def create_row(key, cfg, data, actor):
    values = validate(key, cfg, data, True)
    if cfg["model"].query.filter_by(code=values["code"]).first():
        raise APIError("Duplicate values", 409, {"code": "Code already exists"})
    row = cfg["model"](**values)
    db.session.add(row)
    db.session.commit()
    audit.info("Master created by %s: %s %s", actor.username, key, row.code)
    return row


def update_row(key, cfg, row, data, actor):
    values = validate(key, cfg, data, False, row)
    for col, value in values.items():
        setattr(row, col, value)
    db.session.commit()
    audit.info("Master updated by %s: %s %s fields=%s", actor.username, key, row.code, sorted(values))
    return row


def delete_row(key, cfg, row, actor):
    used = []
    if key == "party":
        products = Product.query.filter(db.or_(Product.supplier == row.code, Product.manufacturer == row.code)).count()
        samples = Sample.query.filter(db.or_(Sample.supplier == row.code, Sample.manufacturer == row.code)).count()
        used = [f"{n} {word}" for n, word in ((products, "product(s)"), (samples, "sample(s)")) if n]
    elif key == "misc" and row.group_name == "Market":
        products = Product.query.filter_by(market=row.code).count()
        used = [f"{products} product(s)"] if products else []
    if used:
        raise APIError(f"{cfg['label']} {row.code} is used by {' and '.join(used)} and cannot be deleted", 409)
    code = row.code
    db.session.delete(row)
    db.session.commit()
    audit.info("Master deleted by %s: %s %s", actor.username, key, code)


def build_query(key, cfg):
    model = cfg["model"]
    query = model.query
    q = (request.args.get("q") or "").strip()
    if q:
        pattern = like_pattern(q)
        columns = ["code", "name"] + [col for col, _ in cfg["fields"].values()]
        query = query.filter(db.or_(*[getattr(model, c).ilike(pattern, escape="\\") for c in columns]))
    for api, (col, _) in cfg["fields"].items():
        value = request.args.get(api)
        if value:
            query = query.filter(getattr(model, col) == value)
    aliases = {api: col for api, (col, _) in cfg["fields"].items()}
    allowed = ("code", "name", *cfg["fields"], "created_at", "updated_at")
    return apply_sort(query, model, allowed, "code", aliases=aliases)
