"""Search endpoints. Same filters as the list routes, kept at the address your spec asks for."""
from flask import Blueprint

from middleware.auth import role_required
from routes.samples import sample_list_response

search_bp = Blueprint("search", __name__)


@search_bp.get("/samples")
@role_required()
def search_samples():
    """?q= ?lab_no= ?material_name= ?batch_no= ?supplier= ?status= plus dates, sorting and paging."""
    return sample_list_response()
