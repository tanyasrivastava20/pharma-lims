"""Sample management. What each role may do is explained in services/sample_service.py."""
from flask import Blueprint
from flask_jwt_extended import current_user

from database import db
from middleware.auth import role_required
from models import Sample
from models.constants import ADMIN, LAB_TECHNICIAN
from services import sample_service as svc
from utils.query import paginate
from utils.responses import APIError, success
from utils.validation import get_json_body

samples_bp = Blueprint("samples", __name__)


def sample_list_response():
    lookups = svc.lookups()
    return success(paginate(svc.build_sample_query(current_user), lambda s: svc.sample_to_dict(s, lookups)))


def get_visible_sample(sample_id):
    """404 (not 403) when the sample is outside the user's scope, so its existence isn't revealed."""
    sample = db.session.get(Sample, sample_id)
    if sample is None or not svc.can_view(sample, current_user):
        raise APIError("Sample not found", 404)
    return sample


@samples_bp.get("")
@role_required()
def list_samples():
    return sample_list_response()


@samples_bp.get("/<int:sample_id>")
@role_required()
def get_sample(sample_id):
    return success(svc.sample_to_dict(get_visible_sample(sample_id), svc.lookups(), detail=True))


@samples_bp.post("")
@role_required(ADMIN, LAB_TECHNICIAN)
def create_sample():
    sample = svc.create_sample(get_json_body(), current_user)
    return success(svc.sample_to_dict(sample, svc.lookups(), detail=True), "Sample created", 201)


@samples_bp.put("/<int:sample_id>")
@role_required(ADMIN, LAB_TECHNICIAN)
def update_sample(sample_id):
    sample = svc.update_sample(get_visible_sample(sample_id), get_json_body(), current_user)
    return success(svc.sample_to_dict(sample, svc.lookups(), detail=True), "Sample updated")


@samples_bp.delete("/<int:sample_id>")
@role_required(ADMIN)
def delete_sample(sample_id):
    sample = get_visible_sample(sample_id)
    lab_no = sample.lab_no
    action = svc.delete_sample(sample, current_user)
    return success({"lab_no": lab_no, "action": action}, f"Sample {lab_no} {action}")
