from datetime import date, timedelta

from flask import request
from sqlalchemy.exc import IntegrityError

from database import db
from models import Packaging, Party, Product, Sample, SampleHistory, User
from models.constants import (ADMIN, CATEGORIES, FINAL_STATUSES, LAB_TECHNICIAN, MATERIAL_TYPES,
                              PACKAGING_UNITS, QUALITY_ANALYST, SAMPLE_STATUSES, UNITS)
from utils.query import apply_sort, bool_arg, like_pattern
from utils.responses import APIError
from utils.validation import clean_bool, clean_date, clean_int, clean_number, clean_text
from utils.logging_setup import audit

TEXT_FIELDS = {"plant": (30, True), "batch_no": (40, True), "ar_no": (40, False),
               "sap_batch_no": (40, False), "sap_lot_no": (40, False)}


# ------------------------------------------------------------------ who can see what
def scope(query, user):
    """Admin sees everything. Analysts see samples assigned to them. Technicians see samples
    assigned to them plus the ones they logged themselves."""
    if user.role == ADMIN:
        return query
    if user.role == QUALITY_ANALYST:
        return query.filter(Sample.analyst == user.username)
    return query.filter(db.or_(Sample.analyst == user.username, Sample.login_by == user.username))


def can_view(sample, user):
    if user.role == ADMIN:
        return True
    if sample.analyst == user.username:
        return True
    return user.role == LAB_TECHNICIAN and sample.login_by == user.username


def add_history(sample, action, actor):
    sample.history.append(SampleHistory(action=action, changed_by=actor.id, changed_by_name=actor.username))


# ------------------------------------------------------------------ validation
def validate_sample(data, creating, sample=None):
    errors, v = {}, {}
    for key in ("status", "analyst", "result"):
        if key in data:
            errors[key] = "Changed through the workflow endpoints"
    if not creating and "lab_no" in data and str(data["lab_no"]).strip().upper() != sample.lab_no:
        errors["lab_no"] = "Lab number is assigned by the system and cannot be changed"

    product = None
    if creating or "material_code" in data:
        code = (clean_text(data, "material_code", 30, errors, True) or "").upper()
        if code and "material_code" not in errors:
            product = Product.query.filter_by(material_code=code).first()
            if product is None:
                errors["material_code"] = "Unknown material code"
            elif product.obsolete and (creating or code != sample.material_code):
                errors["material_code"] = "This material is marked obsolete"
            else:
                v["material_code"], v["material_name"] = code, product.material_name

    for key, required in (("supplier", True), ("manufacturer", False)):
        if creating and key == "supplier" or key in data:
            code = clean_text(data, key, 30, errors, required)
            if code and key not in errors:
                party = Party.query.filter_by(code=code).first()
                if party is None:
                    errors[key] = "Unknown party code"
                else:
                    v[key], v[key + "_name"] = code, party.name
            elif not code and key not in errors:
                v[key], v[key + "_name"] = None, None

    for key, (max_len, required) in TEXT_FIELDS.items():
        if creating or key in data:
            value = clean_text(data, key, max_len, errors, required)
            if key not in errors:
                v[key] = value

    for key, allowed, default in (
            ("material_type", MATERIAL_TYPES, product.material_type if creating and product else None),
            ("category", CATEGORIES, CATEGORIES[0] if creating else None),
            ("unit", UNITS, product.unit if creating and product else None)):
        if key in data:
            if data[key] not in allowed:
                errors[key] = "Must be one of: " + ", ".join(allowed)
            else:
                v[key] = data[key]
        elif default:
            v[key] = default

    if creating or "quantity" in data:
        if data.get("quantity") in (None, ""):
            errors["quantity"] = "Required"
        else:
            quantity = clean_number(data, "quantity", errors)
            if "quantity" not in errors:
                v["quantity"] = quantity
    if "retest_required" in data:
        flag = clean_bool(data, "retest_required", errors)
        if "retest_required" not in errors:
            v["retest_required"] = flag
    elif creating:
        v["retest_required"] = False

    if creating or "login_date" in data:
        login = clean_date(data, "login_date", errors, required="login_date" in data)
        if "login_date" not in errors:
            v["login_date"] = login or date.today()
    for key in ("manufacturing_date", "expiry_date"):
        if key in data:
            value = clean_date(data, key, errors)
            if key not in errors:
                v[key] = value
    if v.get("manufacturing_date") and v["manufacturing_date"] > date.today() + timedelta(days=1):
        errors["manufacturing_date"] = "Cannot be in the future"
    mfg = v.get("manufacturing_date", sample.manufacturing_date if sample else None)
    exp = v.get("expiry_date", sample.expiry_date if sample else None)
    if mfg and exp and "manufacturing_date" not in errors and "expiry_date" not in errors and exp <= mfg:
        errors["expiry_date"] = "Must be after the manufacturing date"

    packaging = None
    if "packaging" in data:
        rows = data["packaging"]
        if not isinstance(rows, list) or len(rows) > 50:
            errors["packaging"] = "Must be a list of at most 50 rows"
        else:
            packaging = []
            for i, row in enumerate(rows):
                if not isinstance(row, dict):
                    errors[f"packaging[{i}]"] = "Must be an object"
                    continue
                row_err = {}
                count = clean_int(row, "count", row_err, 1, 100000) if "count" in row else row_err.setdefault("count", "Required")
                qty = clean_number(row, "quantity", row_err) if "quantity" in row else row_err.setdefault("quantity", "Required")
                unit = row.get("unit", "Kg")
                if unit not in PACKAGING_UNITS:
                    row_err["unit"] = "Must be one of: " + ", ".join(PACKAGING_UNITS)
                if row_err:
                    errors[f"packaging[{i}]"] = row_err
                else:
                    packaging.append(dict(count=count, quantity=qty, unit=unit))
    if errors:
        raise APIError("Validation failed", 400, errors)
    return v, packaging


# ------------------------------------------------------------------ create / update / delete
def next_lab_no():
    last = db.session.query(db.func.max(db.cast(db.func.substr(Sample.lab_no, 3), db.Integer))).scalar() or 0
    return f"LB{last + 1:03d}"


def create_sample(data, actor):
    values, packaging = validate_sample(data, True)
    for attempt in range(3):  # retry if two people grab the same lab number at once
        sample = Sample(lab_no=next_lab_no(), login_by=actor.username, status="Sample Created", **values)
        sample.packaging = [Packaging(**p) for p in packaging or []]
        add_history(sample, "Sample logged", actor)
        db.session.add(sample)
        try:
            db.session.commit()
            break
        except IntegrityError:
            db.session.rollback()
            if attempt == 2:
                raise
    audit.info("Sample created by %s: %s (%s, batch %s)", actor.username, sample.lab_no,
                            sample.material_code, sample.batch_no)
    return sample


def update_sample(sample, data, actor):
    if sample.status in FINAL_STATUSES:
        raise APIError(f"Sample is {sample.status} and can no longer be changed", 409)
    if actor.role == LAB_TECHNICIAN and (sample.login_by != actor.username or sample.status != "Sample Created"):
        raise APIError("Lab Technicians can only edit their own samples that are still at 'Sample Created'", 403)
    values, packaging = validate_sample(data, False, sample)
    for key, value in values.items():
        setattr(sample, key, value)
    if packaging is not None:
        sample.packaging = [Packaging(**p) for p in packaging]
    fields = sorted(list(values) + (["packaging"] if packaging is not None else []))
    if fields:
        add_history(sample, "Sample updated: " + ", ".join(fields), actor)
    db.session.commit()
    audit.info("Sample updated by %s: %s fields=%s", actor.username, sample.lab_no, fields)
    return sample


def delete_sample(sample, actor):
    """Not yet processed -> deleted. In progress -> kept and marked Cancelled. Finished -> refused."""
    if sample.status in FINAL_STATUSES:
        raise APIError(f"Sample is {sample.status} and cannot be deleted", 409)
    lab_no = sample.lab_no
    if sample.status == "Sample Created":
        db.session.delete(sample)
        db.session.commit()
        audit.info("Sample deleted by %s: %s", actor.username, lab_no)
        return "deleted"
    sample.status = "Cancelled"
    add_history(sample, "Sample cancelled", actor)
    db.session.commit()
    audit.info("Sample cancelled by %s: %s", actor.username, lab_no)
    return "cancelled"


# ------------------------------------------------------------------ listing and search
def build_sample_query(user):
    query = scope(Sample.query, user)
    q = (request.args.get("q") or "").strip()
    if q:
        pattern = like_pattern(q)
        query = query.filter(db.or_(*[getattr(Sample, f).ilike(pattern, escape="\\") for f in (
            "lab_no", "material_code", "material_name", "batch_no", "supplier", "supplier_name", "ar_no", "sap_lot_no")]))
    for field in ("lab_no", "material_name", "batch_no"):
        value = (request.args.get(field) or "").strip()
        if value:
            query = query.filter(getattr(Sample, field).ilike(like_pattern(value), escape="\\"))
    supplier = (request.args.get("supplier") or "").strip()
    if supplier:
        pattern = like_pattern(supplier)
        query = query.filter(db.or_(Sample.supplier.ilike(pattern, escape="\\"), Sample.supplier_name.ilike(pattern, escape="\\")))
    status = request.args.get("status")
    if status:
        if status not in SAMPLE_STATUSES:
            raise APIError("'status' must be one of: " + ", ".join(SAMPLE_STATUSES), 400)
        query = query.filter(Sample.status == status)
    for field in ("material_code", "analyst", "plant", "category", "login_by"):
        value = request.args.get(field)
        if value:
            query = query.filter(getattr(Sample, field) == value)
    for param, column, op in (("login_date_from", Sample.login_date, "ge"), ("login_date_to", Sample.login_date, "le"),
                              ("expiry_before", Sample.expiry_date, "lt")):
        if request.args.get(param):
            errors = {}
            value = clean_date(request.args, param, errors)
            if errors:
                raise APIError(f"'{param}' must be a date in YYYY-MM-DD format", 400)
            query = query.filter(getattr(column, f"__{op}__")(value))
    return apply_sort(query, Sample, ("lab_no", "material_name", "batch_no", "supplier_name", "quantity", "login_date",
                                      "expiry_date", "status", "analyst", "created_at", "updated_at"), "created_at", "desc")


def lookups():
    return {"users": dict(db.session.query(User.username, User.full_name).all())}


def sample_to_dict(sample, lk, detail=False):
    data = sample.to_dict(detail=detail)
    data["login_by_name"] = lk["users"].get(sample.login_by)
    data["analyst_name"] = lk["users"].get(sample.analyst)
    if detail:
        data["packed_total"] = sum(p.count * p.quantity for p in sample.packaging)
    return data
