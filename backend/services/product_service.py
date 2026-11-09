import re

from flask import request

from database import db
from models import Miscellaneous, Party, Product, Sample
from models.constants import MATERIAL_TYPES, UNITS
from utils.query import apply_sort, bool_arg, like_pattern
from utils.responses import APIError
from utils.validation import clean_bool, clean_int, clean_text
from utils.logging_setup import audit

CODE_RE = re.compile(r"^[A-Z0-9][A-Z0-9._-]{0,29}$")
# field: (max length, required)
TEXT_FIELDS = {
    "plant": (30, True), "material_name": (150, True), "dosage_form": (40, False), "subgroup": (40, False),
    "market": (30, False), "color": (60, False), "composition": (2000, False), "supplier": (30, False),
    "manufacturer": (30, False), "remarks": (2000, False),
}


def validate_product(data, creating):
    errors, values = {}, {}
    if creating:
        code = (clean_text(data, "material_code", 30, errors, True) or "").upper()
        if code and "material_code" not in errors and not CODE_RE.match(code):
            errors["material_code"] = "Letters, numbers, dot, dash or underscore only"
        values["material_code"] = code
    for key, (max_len, required) in TEXT_FIELDS.items():
        if creating or key in data:
            value = clean_text(data, key, max_len, errors, required)
            if key not in errors:
                values[key] = value
    if creating or "material_type" in data:
        if data.get("material_type") not in MATERIAL_TYPES:
            errors["material_type"] = "Must be one of: " + ", ".join(MATERIAL_TYPES)
        else:
            values["material_type"] = data["material_type"]
    if "unit" in data:
        if data["unit"] not in UNITS:
            errors["unit"] = "Must be one of: " + ", ".join(UNITS)
        else:
            values["unit"] = data["unit"]
    elif creating:
        values["unit"] = "kg"
    if "retest_period" in data:
        months = clean_int(data, "retest_period", errors, 0, 600)
        if "retest_period" not in errors:
            values["retest_period"] = months
    elif creating:
        values["retest_period"] = 12
    if "obsolete" in data:
        flag = clean_bool(data, "obsolete", errors)
        if "obsolete" not in errors:
            values["obsolete"] = flag
    elif creating:
        values["obsolete"] = False
    # codes must exist in the master data
    for key in ("supplier", "manufacturer"):
        if values.get(key) and not Party.query.filter_by(code=values[key]).first():
            errors[key] = "Unknown party code"
    if values.get("market") and not Miscellaneous.query.filter_by(code=values["market"], group_name="Market").first():
        errors["market"] = "Unknown market code"
    if errors:
        raise APIError("Validation failed", 400, errors)
    return values


def create_product(data, actor):
    values = validate_product(data, True)
    if Product.query.filter_by(material_code=values["material_code"]).first():
        raise APIError("Duplicate values", 409, {"material_code": "Material code already exists"})
    product = Product(**values)
    db.session.add(product)
    db.session.commit()
    audit.info("Product created by %s: %s", actor.username, product.material_code)
    return product


def update_product(product, data, actor):
    if "material_code" in data and str(data["material_code"]).strip().upper() != product.material_code:
        raise APIError("Validation failed", 400, {"material_code": "Material code cannot be changed"})
    values = validate_product(data, False)
    for key, value in values.items():
        setattr(product, key, value)
    db.session.commit()
    audit.info("Product updated by %s: %s fields=%s", actor.username, product.material_code, sorted(values))
    return product


def delete_product(product, actor):
    used = Sample.query.filter_by(material_code=product.material_code).count()
    if used:
        raise APIError(f"This material is used by {used} sample(s) and cannot be deleted. "
                       "Mark it as Obsolete instead.", 409)
    code = product.material_code
    db.session.delete(product)
    db.session.commit()
    audit.info("Product deleted by %s: %s", actor.username, code)


def build_product_query():
    query = Product.query
    q = (request.args.get("q") or "").strip()
    if q:
        pattern = like_pattern(q)
        query = query.filter(db.or_(*[getattr(Product, f).ilike(pattern, escape="\\")
                                      for f in ("material_code", "material_name", "supplier", "manufacturer")]))
    for field in ("plant", "material_type", "dosage_form", "subgroup", "market", "supplier", "manufacturer"):
        value = request.args.get(field)
        if value:
            query = query.filter(getattr(Product, field) == value)
    obsolete = bool_arg("obsolete")
    if obsolete is not None:
        query = query.filter(Product.obsolete == obsolete)
    return apply_sort(query, Product, ("material_code", "material_name", "material_type", "plant",
                                       "retest_period", "created_at", "updated_at"), "material_code")


def name_lookups():
    """Code -> name maps, so the frontend can show names next to codes without extra requests."""
    return {
        "party": dict(db.session.query(Party.code, Party.name).all()),
        "market": dict(db.session.query(Miscellaneous.code, Miscellaneous.name)
                       .filter(Miscellaneous.group_name == "Market").all()),
    }


def product_to_dict(product, lookups):
    data = product.to_dict()
    data["supplier_name"] = lookups["party"].get(product.supplier)
    data["manufacturer_name"] = lookups["party"].get(product.manufacturer)
    data["market_name"] = lookups["market"].get(product.market)
    return data
