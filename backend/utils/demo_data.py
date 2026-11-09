"""Sample master data and products so the API has something to show. Used by: python seed.py --demo"""
from datetime import date

from database import db
from models import (Assay, Miscellaneous, Packaging, Party, Product, SampleHistory, Sample, SamplingInspection,
                    Specification, TestCharacteristic, User)

PLANT = "P003-PIL-III"


def _product(code, name, mtype, sub, market, retest, party):
    return dict(plant=PLANT, material_code=code, material_name=name, material_type=mtype, dosage_form="R-Raw Material",
                subgroup=sub, unit="kg", market=market, retest_period=retest, supplier=party, manufacturer=party)


DEMO = [
    (Party, [dict(code="0010034314", name="AUROACTIVE PHARMA PVT LTD", city="Hyderabad"),
             dict(code="0010034420", name="SUNRISE CHEMICALS", city="Mumbai"),
             dict(code="0010035001", name="MEDIPACK INDUSTRIES", city="Baddi")]),
    (Miscellaneous, [dict(code="MM001", name="Domestic", group_name="Market"),
                     dict(code="MM002", name="Export", group_name="Market"),
                     dict(code="MM003", name="NA", group_name="Market")]),
    (TestCharacteristic, [dict(code="T001", name="Description", test_type="Qualitative", unit="-"),
                          dict(code="T002", name="Assay", test_type="Quantitative", unit="%"),
                          dict(code="T003", name="Loss on Drying", test_type="Quantitative", unit="%")]),
    (Assay, [dict(code="A001", name="Paracetamol assay by HPLC", method="HPLC", limit_range="99.0 - 101.0 %")]),
    (SamplingInspection, [dict(code="S001", name="Raw material sampling", plan="sqrt(n)+1", level="II")]),
    (Product, [_product("10000942", "PARACETAMOL IP", "R-Raw Material", "A-API", "MM003", 12, "0010034314"),
               _product("10000943", "MICROCRYSTALLINE CELLULOSE IP", "R-Raw Material", "E-Excipient", "MM001", 24, "0010034420"),
               _product("20000117", "ALU-PVC BLISTER FOIL", "P-Packing Material", "PK-Packing", "MM001", 18, "0010035001")]),
    (Specification, [dict(code="SP-PARA-01", name="Paracetamol IP specification", material_code="10000942", version="1.0")]),
]


SAMPLES = [  # lab no, material, batch, qty, status, analyst username, result
    ("LB001", "10000942", "2530401555", 2000, "Sample Created", None, None),
    ("LB002", "10000943", "2530401556", 1500, "Sample Received", None, None),
    ("LB003", "10000942", "2530401557", 1000, "Testing Assigned", "analyst", None),
    ("LB004", "10000942", "2530401558", 500, "Analysis Completed", "analyst", "Assay 99.6 % - complies"),
]


def seed_demo_samples():
    users = {u.username for u in User.query.all()}
    added = 0
    for lab, code, batch, qty, status, analyst, result in SAMPLES:
        if Sample.query.filter_by(lab_no=lab).first():
            continue
        p = Product.query.filter_by(material_code=code).first()
        party = Party.query.filter_by(code=p.supplier).first()
        s = Sample(lab_no=lab, plant=PLANT, login_date=date(2026, 11, 2), material_code=code, material_name=p.material_name,
                   supplier=p.supplier, supplier_name=party.name, manufacturer=p.manufacturer, manufacturer_name=party.name,
                   ar_no="AR-" + lab[2:], batch_no=batch, sap_batch_no="0000" + batch, manufacturing_date=date(2026, 9, 1),
                   expiry_date=date(2029, 8, 31), material_type=p.material_type, category="00-Normal Login",
                   sap_lot_no="01000043" + lab[2:], login_by="technician" if "technician" in users else None,
                   quantity=qty, unit="kg", status=status, analyst=analyst if analyst in users else None, result=result)
        s.packaging = [Packaging(count=qty // 25, quantity=25, unit="Kg")]
        s.history = [SampleHistory(action="Sample logged (demo data)", changed_by_name="system")]
        db.session.add(s)
        added += 1
    db.session.commit()
    return added


def seed_demo(samples=True):
    """Adds anything missing (matched by code). Safe to run repeatedly. Returns how many rows were added."""
    added = 0
    for model, rows in DEMO:
        key = "material_code" if model is Product else "code"
        for row in rows:
            if not model.query.filter_by(**{key: row[key]}).first():
                db.session.add(model(**row))
                added += 1
        db.session.commit()
    return added + (seed_demo_samples() if samples else 0)
