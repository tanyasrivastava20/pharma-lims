"""Workflow actions on a sample. Who may do what:
   receive          Admin, Lab Technician
   assign           Admin
   observe          Admin, Quality Analyst, Lab Technician (only on samples assigned to them;
                    technicians can record a result but not complete the analysis)
   approve/reject   Admin
"""
from flask import Blueprint
from flask_jwt_extended import current_user

from database import db
from middleware.auth import role_required
from models import Sample
from models.constants import ADMIN, LAB_TECHNICIAN, QUALITY_ANALYST, SAMPLE_STATUSES
from routes.samples import get_visible_sample
from services import sample_service, workflow_service
from utils.responses import success
from utils.validation import get_json_body

workflow_bp = Blueprint("workflow", __name__)


def _respond(sample, message):
    return success(sample_service.sample_to_dict(sample, sample_service.lookups(), detail=True), message)


@workflow_bp.get("/summary")
@role_required()
def summary():
    """How many samples are at each status (only the ones this user may see). For dashboards."""
    query = sample_service.scope(db.session.query(Sample.status, db.func.count(Sample.id)), current_user)
    found = dict(query.group_by(Sample.status).all())
    counts = {status: found.get(status, 0) for status in SAMPLE_STATUSES}
    return success({"counts": counts, "total": sum(counts.values())})


@workflow_bp.post("/<int:sample_id>/receive")
@role_required(ADMIN, LAB_TECHNICIAN)
def receive(sample_id):
    sample = get_visible_sample(sample_id)
    workflow_service.receive(sample, current_user)
    return _respond(sample, f"Sample {sample.lab_no} received")


@workflow_bp.post("/<int:sample_id>/assign")
@role_required(ADMIN)
def assign(sample_id):
    sample = get_visible_sample(sample_id)
    workflow_service.assign(sample, get_json_body(), current_user)
    return _respond(sample, f"Sample {sample.lab_no} assigned to {sample.analyst}")


@workflow_bp.post("/<int:sample_id>/observe")
@role_required(ADMIN, QUALITY_ANALYST, LAB_TECHNICIAN)
def observe(sample_id):
    sample = get_visible_sample(sample_id)
    workflow_service.observe(sample, get_json_body(), current_user)
    done = sample.status == "Analysis Completed"
    return _respond(sample, f"Analysis completed for {sample.lab_no}" if done else f"Observation saved for {sample.lab_no}")


@workflow_bp.post("/<int:sample_id>/approve")
@role_required(ADMIN)
def approve(sample_id):
    sample = get_visible_sample(sample_id)
    workflow_service.approve(sample, get_json_body(optional=True), current_user)
    return _respond(sample, f"Sample {sample.lab_no} approved")


@workflow_bp.post("/<int:sample_id>/reject")
@role_required(ADMIN)
def reject(sample_id):
    sample = get_visible_sample(sample_id)
    workflow_service.reject(sample, get_json_body(), current_user)
    return _respond(sample, f"Sample {sample.lab_no} rejected")
