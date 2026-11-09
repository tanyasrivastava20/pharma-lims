"""The six master-data tables. Each has a unique code and a name, plus a few extra columns."""
from database import db
from models.base import DictMixin, TimestampMixin


class MasterBase(db.Model, TimestampMixin, DictMixin):
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(30), unique=True, nullable=False, index=True)
    name = db.Column(db.String(150), nullable=False)


class Party(MasterBase):                       # suppliers and manufacturers
    __tablename__ = "parties"
    city = db.Column(db.String(80))


class TestCharacteristic(MasterBase):
    __tablename__ = "test_characteristics"
    test_type = db.Column(db.String(30))       # Qualitative / Quantitative
    unit = db.Column(db.String(20))


class Miscellaneous(MasterBase):
    __tablename__ = "miscellaneous"
    group_name = db.Column(db.String(40))      # e.g. Market


class Assay(MasterBase):
    __tablename__ = "assays"
    method = db.Column(db.String(60))
    limit_range = db.Column(db.String(60))


class SamplingInspection(MasterBase):
    __tablename__ = "sampling_inspections"
    plan = db.Column(db.String(60))
    level = db.Column(db.String(20))


class Specification(MasterBase):
    __tablename__ = "specifications"
    material_code = db.Column(db.String(30), db.ForeignKey("products.material_code", ondelete="SET NULL"))
    version = db.Column(db.String(20))


# URL name -> model, used by the master-data API
MASTER_MODELS = {
    "party": Party,
    "test": TestCharacteristic,
    "misc": Miscellaneous,
    "assay": Assay,
    "sampling": SamplingInspection,
    "spec": Specification,
}
