"""Fixed lists shared by the models, routes and validation."""
ROLES = ("Admin", "Quality Analyst", "Lab Technician")

SAMPLE_STATUSES = (
    "Sample Created",
    "Sample Received",
    "Testing Assigned",
    "Analysis Completed",
    "Approved",
    "Rejected",
    "Cancelled",
)


def sql_in_list(values):
    """('a', 'b') -> "'a', 'b'" for use inside a CHECK constraint."""
    return ", ".join("'" + v.replace("'", "''") + "'" for v in values)

ADMIN, QUALITY_ANALYST, LAB_TECHNICIAN = ROLES

MATERIAL_TYPES = ("R-Raw Material", "P-Packing Material", "F-Finished Product")
UNITS = ("kg", "g", "L", "mL", "Nos")

CATEGORIES = ("00-Normal Login", "01-Retest", "02-Stability")
PACKAGING_UNITS = ("Kg", "g", "L")
FINAL_STATUSES = ("Approved", "Rejected", "Cancelled")

TEST_TYPES = ("Qualitative", "Quantitative")
