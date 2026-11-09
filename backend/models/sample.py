from sqlalchemy import CheckConstraint

from database import db
from models.base import DictMixin, TimestampMixin, utcnow
from models.constants import SAMPLE_STATUSES, sql_in_list


class Sample(db.Model, TimestampMixin, DictMixin):
    __tablename__ = "samples"
    __table_args__ = (
        CheckConstraint(f"status IN ({sql_in_list(SAMPLE_STATUSES)})", name="ck_samples_status"),
        CheckConstraint("quantity >= 0", name="ck_samples_quantity"),
        CheckConstraint(
            "expiry_date IS NULL OR manufacturing_date IS NULL OR expiry_date > manufacturing_date",
            name="ck_samples_dates",
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    lab_no = db.Column(db.String(20), unique=True, nullable=False, index=True)
    plant = db.Column(db.String(30), nullable=False)
    login_date = db.Column(db.Date, nullable=False)
    material_code = db.Column(db.String(30), db.ForeignKey("products.material_code", ondelete="RESTRICT"),
                              nullable=False, index=True)
    material_name = db.Column(db.String(150), nullable=False)   # copied at login time
    supplier = db.Column(db.String(30), index=True)             # Party Master code
    supplier_name = db.Column(db.String(150))                   # copied at login time
    manufacturer = db.Column(db.String(30))
    manufacturer_name = db.Column(db.String(150))
    ar_no = db.Column(db.String(40))
    batch_no = db.Column(db.String(40), nullable=False, index=True)
    sap_batch_no = db.Column(db.String(40))
    manufacturing_date = db.Column(db.Date)
    expiry_date = db.Column(db.Date)
    material_type = db.Column(db.String(40))
    category = db.Column(db.String(40))
    sap_lot_no = db.Column(db.String(40))
    login_by = db.Column(db.String(100))
    quantity = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(20), nullable=False, default="kg")
    retest_required = db.Column(db.Boolean, nullable=False, default=False)
    analyst = db.Column(db.String(50))                          # username of the assigned analyst
    result = db.Column(db.Text)
    status = db.Column(db.String(30), nullable=False, default="Sample Created", index=True)

    packaging = db.relationship("Packaging", back_populates="sample", cascade="all, delete-orphan",
                                passive_deletes=True, order_by="Packaging.id")
    history = db.relationship("SampleHistory", back_populates="sample", cascade="all, delete-orphan",
                              passive_deletes=True, order_by="SampleHistory.id")

    def to_dict(self, detail=True):
        data = DictMixin.to_dict(self)
        if detail:
            data["packaging"] = [p.to_dict() for p in self.packaging]
            data["history"] = [h.to_dict() for h in self.history]
        return data


class Packaging(db.Model, DictMixin):
    __tablename__ = "packaging"

    id = db.Column(db.Integer, primary_key=True)
    sample_id = db.Column(db.Integer, db.ForeignKey("samples.id", ondelete="CASCADE"), nullable=False, index=True)
    count = db.Column(db.Integer, nullable=False)        # number of containers
    quantity = db.Column(db.Float, nullable=False)       # quantity per container
    unit = db.Column(db.String(10), nullable=False, default="Kg")

    sample = db.relationship("Sample", back_populates="packaging")


class SampleHistory(db.Model, DictMixin):
    __tablename__ = "sample_history"

    id = db.Column(db.Integer, primary_key=True)
    sample_id = db.Column(db.Integer, db.ForeignKey("samples.id", ondelete="CASCADE"), nullable=False, index=True)
    action = db.Column(db.String(255), nullable=False)
    changed_by = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"))
    changed_by_name = db.Column(db.String(50))           # kept even if the user is deleted later
    timestamp = db.Column(db.DateTime, nullable=False, default=utcnow)

    sample = db.relationship("Sample", back_populates="history")
