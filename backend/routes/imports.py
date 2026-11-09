"""CSV imports (Admin only) for products and master data.
   ?dry_run=true   only check the file, change nothing
   ?mode=create    (default) every row must be a NEW code
   ?mode=upsert    existing codes are updated, new ones are created
Samples are not imported: they must go through the workflow (login, receipt, testing...)."""
from flask import Blueprint, request

from middleware.auth import role_required
from models import Product
from models.constants import ADMIN
from routes.exports import PRODUCT_COLUMNS
from services import csv_service, master_service, product_service
from utils.query import bool_arg
from utils.responses import APIError, success

imports_bp = Blueprint("imports", __name__)


def _options():
    mode = request.args.get("mode", "create").lower()
    if mode not in ("create", "upsert"):
        raise APIError("'mode' must be create or upsert", 400)
    return mode, bool(bool_arg("dry_run"))


def _reply(result, noun):
    if result["dry_run"]:
        return success(result, f"Check passed: {result['to_create']} new and {result['to_update']} existing {noun} can be imported")
    return success(result, f"Imported {result['rows']} {noun}: {result['to_create']} created, {result['to_update']} updated",
                   201 if result["to_create"] else 200)


@imports_bp.post("/products")
@role_required(ADMIN)
def import_products():
    mode, dry_run = _options()
    rows, ignored = csv_service.read_upload(["material_code", "material_name", "plant", "material_type"], PRODUCT_COLUMNS)
    result = csv_service.run_import(
        rows, "material_code",
        find_existing=lambda code: Product.query.filter_by(material_code=code).first(),
        validate=lambda data, existing: product_service.validate_product(data, existing is None),
        build=lambda values: Product(**values),
        apply_update=lambda row, values: [setattr(row, k, v) for k, v in values.items()],
        mode=mode, dry_run=dry_run, bool_cols=("obsolete",), label="products")
    result["ignored_columns"] = ignored
    return _reply(result, "product(s)")


@imports_bp.post("/master/<kind>")
@role_required(ADMIN)
def import_master(kind):
    key, cfg = master_service.resolve(kind)
    mode, dry_run = _options()
    columns = ["code", "name", *cfg["fields"]]
    rows, ignored = csv_service.read_upload(["code", "name"], columns)
    model = cfg["model"]
    result = csv_service.run_import(
        rows, "code",
        find_existing=lambda code: model.query.filter_by(code=code).first(),
        validate=lambda data, existing: master_service.validate(key, cfg, data, existing is None, existing),
        build=lambda values: model(**values),
        apply_update=lambda row, values: [setattr(row, k, v) for k, v in values.items()],
        mode=mode, dry_run=dry_run, label="master " + key)
    result["ignored_columns"] = ignored
    return _reply(result, "record(s)")
