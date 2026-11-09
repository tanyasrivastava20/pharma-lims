"""Master data CRUD. Everyone logged in can read; only Admin can change.
/api/master/<type>  where type is: party, test, misc, assay, sampling or spec
(long names such as parties, test-characteristics, miscellaneous also work)."""
from flask import Blueprint
from flask_jwt_extended import current_user

from middleware.auth import role_required
from models.constants import ADMIN
from services import master_service as svc
from utils.query import paginate
from utils.responses import APIError, success
from utils.validation import get_json_body

master_bp = Blueprint("master", __name__)


def _get_row(cfg, row_id):
    row = cfg["model"].query.get(row_id)
    if row is None:
        raise APIError(f"{cfg['label']} not found", 404)
    return row


@master_bp.get("/<kind>")
@role_required()
def list_rows(kind):
    key, cfg = svc.resolve(kind)
    return success(paginate(svc.build_query(key, cfg), lambda r: svc.to_api(r, cfg)))


@master_bp.get("/<kind>/<int:row_id>")
@role_required()
def get_row(kind, row_id):
    key, cfg = svc.resolve(kind)
    return success(svc.to_api(_get_row(cfg, row_id), cfg))


@master_bp.post("/<kind>")
@role_required(ADMIN)
def create_row(kind):
    key, cfg = svc.resolve(kind)
    row = svc.create_row(key, cfg, get_json_body(), current_user)
    return success(svc.to_api(row, cfg), f"{cfg['label']} created", 201)


@master_bp.put("/<kind>/<int:row_id>")
@role_required(ADMIN)
def update_row(kind, row_id):
    key, cfg = svc.resolve(kind)
    row = svc.update_row(key, cfg, _get_row(cfg, row_id), get_json_body(), current_user)
    return success(svc.to_api(row, cfg), f"{cfg['label']} updated")


@master_bp.delete("/<kind>/<int:row_id>")
@role_required(ADMIN)
def delete_row(kind, row_id):
    key, cfg = svc.resolve(kind)
    svc.delete_row(key, cfg, _get_row(cfg, row_id), current_user)
    return success(message=f"{cfg['label']} deleted")
