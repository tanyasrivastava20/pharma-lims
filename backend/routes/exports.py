"""Downloads. Add ?format=pdf to any list export for a PDF instead of a CSV file.
They follow the same filters, sorting and visibility rules as the list endpoints."""
from flask import Blueprint, request
from flask_jwt_extended import current_user
from sqlalchemy.orm import selectinload

from middleware.auth import role_required
from models import Sample
from routes.samples import get_visible_sample
from services import csv_service, master_service, pdf_service, product_service, sample_service
from utils.logging_setup import audit
from utils.responses import APIError

exports_bp = Blueprint("exports", __name__)

SAMPLE_COLUMNS = ["lab_no", "plant", "login_date", "material_code", "material_name", "supplier", "supplier_name",
                  "manufacturer", "manufacturer_name", "ar_no", "batch_no", "sap_batch_no", "manufacturing_date",
                  "expiry_date", "material_type", "category", "sap_lot_no", "login_by", "quantity", "unit",
                  "retest_required", "analyst", "result", "status", "packaging", "created_at", "updated_at"]
PRODUCT_COLUMNS = ["plant", "material_code", "material_name", "material_type", "dosage_form", "subgroup", "unit", "market",
                   "retest_period", "color", "composition", "supplier", "manufacturer", "remarks", "obsolete"]
# (key, heading, relative width) for the PDF tables
SAMPLE_PDF = [("lab_no", "Lab No", 7), ("material_name", "Material", 17), ("batch_no", "Batch No", 10),
              ("supplier_name", "Supplier", 15), ("qty_unit", "Quantity", 8), ("login_date", "Login date", 9),
              ("expiry_date", "Expiry", 9), ("status", "Status", 12), ("analyst", "Analyst", 8)]
PRODUCT_PDF = [("material_code", "Code", 9), ("material_name", "Name", 22), ("material_type", "Type", 14), ("unit", "Unit", 5),
               ("market", "Market", 7), ("retest_period", "Retest (months)", 8), ("supplier", "Supplier", 11),
               ("manufacturer", "Manufacturer", 11), ("obsolete", "Obsolete", 7)]


def _format():
    fmt = request.args.get("format", "csv").lower()
    if fmt not in ("csv", "pdf"):
        raise APIError("'format' must be csv or pdf", 400)
    return fmt


def _filters_text():
    shown = [f"{k} = {v}" for k, v in request.args.items() if v and k not in ("format", "sort", "order", "page", "per_page")]
    return "Filters: " + ("; ".join(shown) if shown else "none")


def _all_rows(query, fmt):
    limit = pdf_service.MAX_PDF_ROWS if fmt == "pdf" else csv_service.MAX_EXPORT_ROWS
    if query.order_by(None).count() > limit:
        hint = " Use the CSV export or narrow the filter." if fmt == "pdf" else " Narrow the filter."
        raise APIError(f"Too many rows to export as {fmt.upper()} (limit {limit}).{hint}", 400)
    return query.all()


def _deliver(fmt, rows, columns, pdf_columns, name, title):
    audit.info("Export %s: %s rows=%s %s", fmt.upper(), name, len(rows), _filters_text())
    if fmt == "pdf":
        subtitle = f"{len(rows)} record(s)  |  {_filters_text()}"
        return pdf_service.pdf_response(pdf_service.table_pdf(title, subtitle, pdf_columns, rows, current_user), name)
    return csv_service.csv_response(rows, columns, name)


@exports_bp.get("/samples")
@role_required()
def export_samples():
    """Same filters as GET /api/samples (?status= ?q= ?batch_no= ...). Only samples you may see."""
    fmt = _format()
    rows = []
    for sample in _all_rows(sample_service.build_sample_query(current_user).options(selectinload(Sample.packaging)), fmt):
        d = sample.to_dict(detail=False)
        d["packaging"] = "; ".join(f"{p.count} x {p.quantity:g} {p.unit}" for p in sample.packaging)
        d["qty_unit"] = f"{pdf_service._fmt(sample.quantity)} {sample.unit}"
        rows.append(d)
    return _deliver(fmt, rows, SAMPLE_COLUMNS, SAMPLE_PDF, "samples", "Samples")


@exports_bp.get("/samples/<int:sample_id>")
@role_required()
def export_sample_report(sample_id):
    """A printable one-sample report (PDF): details, result, packaging and full history."""
    sample = get_visible_sample(sample_id)
    data = sample_service.sample_to_dict(sample, sample_service.lookups(), detail=True)
    audit.info("Export PDF: sample report %s", sample.lab_no)
    return pdf_service.pdf_response(pdf_service.sample_report_pdf(data, current_user), f"sample_{sample.lab_no}")


@exports_bp.get("/products")
@role_required()
def export_products():
    fmt = _format()
    rows = [p.to_dict() for p in _all_rows(product_service.build_product_query(), fmt)]
    return _deliver(fmt, rows, PRODUCT_COLUMNS, PRODUCT_PDF, "products", "Products / Materials")


@exports_bp.get("/master/<kind>")
@role_required()
def export_master(kind):
    key, cfg = master_service.resolve(kind)
    fmt = _format()
    rows = [master_service.to_api(r, cfg) for r in _all_rows(master_service.build_query(key, cfg), fmt)]
    columns = ["code", "name", *cfg["fields"]]
    widths = [10, 30] + [16] * len(cfg["fields"])
    pdf_columns = [(c, c.replace("_", " ").capitalize(), w) for c, w in zip(columns, widths)]
    return _deliver(fmt, rows, columns, pdf_columns, "master_" + key, "Master data: " + cfg["label"])
