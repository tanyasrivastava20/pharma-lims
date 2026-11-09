from sqlalchemy import CheckConstraint

from database import db
from models.base import DictMixin, TimestampMixin


class Product(db.Model, TimestampMixin, DictMixin):
    """Product / Material Master."""

    __tablename__ = "products"
    __table_args__ = (CheckConstraint("retest_period >= 0", name="ck_products_retest"),)

    id = db.Column(db.Integer, primary_key=True)
    plant = db.Column(db.String(30), nullable=False)
    material_code = db.Column(db.String(30), unique=True, nullable=False, index=True)
    material_name = db.Column(db.String(150), nullable=False)
    material_type = db.Column(db.String(40), nullable=False)
    dosage_form = db.Column(db.String(40))
    subgroup = db.Column(db.String(40))
    unit = db.Column(db.String(20), nullable=False, default="kg")
    market = db.Column(db.String(30))          # code from the Miscellaneous master
    retest_period = db.Column(db.Integer, nullable=False, default=12)  # months
    color = db.Column(db.String(60))
    composition = db.Column(db.Text)
    supplier = db.Column(db.String(30))        # Party Master code
    manufacturer = db.Column(db.String(30))    # Party Master code
    remarks = db.Column(db.Text)
    obsolete = db.Column(db.Boolean, nullable=False, default=False)
