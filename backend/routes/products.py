"""Product / Material Master. Everyone logged in can read; only Admin can change."""
from flask import Blueprint
from flask_jwt_extended import current_user

from database import db
from middleware.auth import role_required
from models import Product
from models.constants import ADMIN
from services import product_service as svc
from utils.query import paginate
from utils.responses import APIError, success
from utils.validation import get_json_body

products_bp = Blueprint("products", __name__)


def _get_product(product_id):
    product = db.session.get(Product, product_id)
    if product is None:
        raise APIError("Product not found", 404)
    return product


@products_bp.get("")
@role_required()
def list_products():
    lookups = svc.name_lookups()
    return success(paginate(svc.build_product_query(), lambda p: svc.product_to_dict(p, lookups)))


@products_bp.get("/<int:product_id>")
@role_required()
def get_product(product_id):
    return success(svc.product_to_dict(_get_product(product_id), svc.name_lookups()))


@products_bp.post("")
@role_required(ADMIN)
def create_product():
    product = svc.create_product(get_json_body(), current_user)
    return success(svc.product_to_dict(product, svc.name_lookups()), "Product created", 201)


@products_bp.put("/<int:product_id>")
@role_required(ADMIN)
def update_product(product_id):
    product = svc.update_product(_get_product(product_id), get_json_body(), current_user)
    return success(svc.product_to_dict(product, svc.name_lookups()), "Product updated")


@products_bp.delete("/<int:product_id>")
@role_required(ADMIN)
def delete_product(product_id):
    svc.delete_product(_get_product(product_id), current_user)
    return success(message="Product deleted")
