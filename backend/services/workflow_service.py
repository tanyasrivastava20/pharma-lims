"""Sample workflow:  Created -> Received -> Testing Assigned -> Analysis Completed -> Approved / Rejected.
Every status change adds a history record (who, what, when)."""

from database import db
from models import User
from models.constants import ADMIN, LAB_TECHNICIAN, QUALITY_ANALYST
from services.sample_service import add_history
from utils.responses import APIError
from utils.validation import clean_bool, clean_text
from utils.logging_setup import audit


def _move(sample, expected, new_status, actor, note=""):
    if sample.status != expected:
        raise APIError(f"Sample {sample.lab_no} is '{sample.status}'; this action needs '{expected}'", 409)
    old = sample.status
    sample.status = new_status
    add_history(sample, f"Status: {old} -> {new_status}" + (f" ({note})" if note else ""), actor)
    return old


def _commit(sample, actor, old_status):
    db.session.commit()
    audit.info("Workflow: %s %s -> %s by %s (%s)", sample.lab_no, old_status, sample.status,
                            actor.username, actor.role)


def receive(sample, actor):
    old = _move(sample, "Sample Created", "Sample Received", actor)
    _commit(sample, actor, old)


def assign(sample, data, actor):
    errors = {}
    username = (clean_text(data, "analyst", 50, errors, True) or "").lower()
    if errors:
        raise APIError("Validation failed", 400, errors)
    user = User.query.filter_by(username=username).first()
    if user is None or not user.is_active or user.role not in (QUALITY_ANALYST, LAB_TECHNICIAN):
        raise APIError("Validation failed", 400, {"analyst": "Must be an active Quality Analyst or Lab Technician"})
    old = _move(sample, "Sample Received", "Testing Assigned", actor, f"analyst: {user.username}")
    sample.analyst = user.username
    _commit(sample, actor, old)


def observe(sample, data, actor):
    """Records the test result. With "complete": false the result is saved and the sample stays at
    Testing Assigned; otherwise the analysis is completed and the sample moves on to review."""
    if sample.status != "Testing Assigned":
        raise APIError(f"Sample {sample.lab_no} is '{sample.status}'; this action needs 'Testing Assigned'", 409)
    if actor.role != ADMIN and sample.analyst != actor.username:
        raise APIError("Only the assigned analyst can record observations", 403)
    errors = {}
    result = clean_text(data, "result", 2000, errors, True)
    complete = clean_bool(data, "complete", errors) if "complete" in data else True
    if errors:
        raise APIError("Validation failed", 400, errors)
    if actor.role == LAB_TECHNICIAN and complete:
        raise APIError("Lab Technicians can record observations, but only a Quality Analyst or Admin "
                       "can complete the analysis", 403)
    sample.result = result
    if complete:
        old = _move(sample, "Testing Assigned", "Analysis Completed", actor, "result recorded")
    else:
        old = sample.status
        add_history(sample, "Observation recorded (status unchanged)", actor)
    _commit(sample, actor, old)


def approve(sample, data, actor):
    errors = {}
    remarks = clean_text(data, "remarks", 200, errors)
    if errors:
        raise APIError("Validation failed", 400, errors)
    old = _move(sample, "Analysis Completed", "Approved", actor, remarks or "")
    _commit(sample, actor, old)


def reject(sample, data, actor):
    errors = {}
    reason = clean_text(data, "reason", 200, errors, True)
    if errors:
        raise APIError("Validation failed", 400, errors)
    old = _move(sample, "Analysis Completed", "Rejected", actor, reason)
    _commit(sample, actor, old)
