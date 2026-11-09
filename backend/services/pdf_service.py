"""PDF reports built with ReportLab: list tables (landscape) and a one-sample report (portrait).
Text is limited to Latin characters (the built-in PDF fonts); anything else shows as '?'."""
import io
from datetime import date, datetime
from functools import partial
from xml.sax.saxutils import escape

from flask import Response
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

MAX_PDF_ROWS = 5000
NAVY = colors.HexColor("#0f3d68")
LIGHT = colors.HexColor("#eef2f7")
LINE = colors.HexColor("#c9d3df")
GREY = colors.HexColor("#5b6b7d")

_TITLE = ParagraphStyle("t", fontName="Helvetica-Bold", fontSize=16, textColor=NAVY, leading=20)
_META = ParagraphStyle("m", fontName="Helvetica", fontSize=8, textColor=GREY, leading=11)
_HEAD = ParagraphStyle("h", fontName="Helvetica-Bold", fontSize=7.5, textColor=colors.white, leading=9)
_CELL = ParagraphStyle("c", fontName="Helvetica", fontSize=7.5, leading=9.5)
_LABEL = ParagraphStyle("l", fontName="Helvetica-Bold", fontSize=8.5, textColor=GREY, leading=11)
_VALUE = ParagraphStyle("v", fontName="Helvetica", fontSize=9, leading=11.5)
_SECTION = ParagraphStyle("s", fontName="Helvetica-Bold", fontSize=11, textColor=NAVY, leading=14, spaceBefore=8, spaceAfter=4)


def _fmt(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        return "Yes" if value else "No"
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, float):
        return f"{value:.6f}".rstrip("0").rstrip(".")
    return str(value)


def _safe(value):
    text = _fmt(value).encode("cp1252", "replace").decode("cp1252")
    return escape(text)


class _NumberedCanvas(canvas.Canvas):
    """Adds 'Page X of Y' and a footer line to every page."""

    def __init__(self, *args, footer_text="", **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_pages, self._footer = [], footer_text

    def showPage(self):
        self._saved_pages.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        total = len(self._saved_pages)
        for state in self._saved_pages:
            self.__dict__.update(state)
            width = self._pagesize[0]
            self.setStrokeColor(LINE)
            self.line(14 * mm, 12 * mm, width - 14 * mm, 12 * mm)
            self.setFont("Helvetica", 7.5)
            self.setFillColor(GREY)
            self.drawString(14 * mm, 8 * mm, self._footer)
            self.drawRightString(width - 14 * mm, 8 * mm, f"Page {self._pageNumber} of {total}")
            super().showPage()
        super().save()


def _build(story, page, title, user):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=page, leftMargin=14 * mm, rightMargin=14 * mm, topMargin=14 * mm,
                            bottomMargin=18 * mm, title=title, author="PharmaLIMS 4.0")
    footer = _safe(f"PharmaLIMS 4.0  |  Generated {datetime.now():%Y-%m-%d %H:%M} by {user.username} ({user.role})")
    doc.build(story, canvasmaker=partial(_NumberedCanvas, footer_text=footer.replace("&amp;", "&")))
    return buf.getvalue(), doc.width


def table_pdf(title, subtitle, columns, rows, user):
    """columns: [(key, heading, relative width)], rows: list of dicts."""
    page = landscape(A4)
    story = [Paragraph(_safe(title), _TITLE), Paragraph(_safe(subtitle), _META), Spacer(1, 4 * mm)]
    if not rows:
        story.append(Paragraph("No records match.", _CELL))
    else:
        data = [[Paragraph(_safe(label), _HEAD) for _, label, _ in columns]]
        data += [[Paragraph(_safe(r.get(key)), _CELL) for key, _, _ in columns] for r in rows]
        width = page[0] - 28 * mm
        total = sum(w for _, _, w in columns)
        table = Table(data, colWidths=[width * w / total for _, _, w in columns], repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), NAVY), ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.25, LINE), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT]),
            ("LEFTPADDING", (0, 0), (-1, -1), 4), ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
        story.append(table)
    pdf, _ = _build(story, page, title, user)
    return pdf


def sample_report_pdf(s, user):
    """s: the sample as returned by sample_to_dict(detail=True)."""
    def party(code, name):
        return f"{code} - {name}" if code and name else (code or "")
    pairs = [
        ("Lab No", s["lab_no"]), ("Status", s["status"]),
        ("Plant", s["plant"]), ("Login date", s["login_date"]),
        ("Material", party(s["material_code"], s["material_name"])), ("Material type", s["material_type"]),
        ("Supplier", party(s["supplier"], s["supplier_name"])), ("Manufacturer", party(s["manufacturer"], s["manufacturer_name"])),
        ("AR No", s["ar_no"]), ("Category", s["category"]),
        ("Batch No", s["batch_no"]), ("SAP batch No", s["sap_batch_no"]),
        ("Manufacturing date", s["manufacturing_date"]), ("Expiry date", s["expiry_date"]),
        ("SAP lot No", s["sap_lot_no"]), ("Retest required", s["retest_required"]),
        ("Quantity", f"{_fmt(s['quantity'])} {s['unit']}"), ("Packed in total", _fmt(s["packed_total"])),
        ("Logged by", s.get("login_by_name") or s["login_by"]), ("Analyst", s.get("analyst_name") or s["analyst"]),
    ]
    page = A4
    width = page[0] - 28 * mm
    kv = []
    for i in range(0, len(pairs), 2):
        row = []
        for label, value in pairs[i:i + 2]:
            row += [Paragraph(_safe(label), _LABEL), Paragraph(_safe(value), _VALUE)]
        kv.append(row)
    details = Table(kv, colWidths=[width * 0.17, width * 0.33, width * 0.17, width * 0.33])
    details.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOX", (0, 0), (-1, -1), 0.5, LINE),
                                 ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, LIGHT]),
                                 ("TOPPADDING", (0, 0), (-1, -1), 4), ("BOTTOMPADDING", (0, 0), (-1, -1), 4)]))
    story = [Paragraph(_safe(f"Sample Report - {s['lab_no']}"), _TITLE),
             Paragraph(_safe(f"{s['material_name']}  |  Batch {s['batch_no']}  |  Status: {s['status']}"), _META),
             Spacer(1, 4 * mm), details,
             Paragraph("Test result", _SECTION),
             Paragraph(_safe(s["result"]) if s["result"] else "No result recorded yet.", _VALUE)]

    def grid(head, body, widths):
        data = [[Paragraph(_safe(h), _HEAD) for h in head]] + [[Paragraph(_safe(c), _CELL) for c in row] for row in body]
        t = Table(data, colWidths=[width * w for w in widths], repeatRows=1)
        t.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), NAVY), ("GRID", (0, 0), (-1, -1), 0.25, LINE),
                               ("VALIGN", (0, 0), (-1, -1), "TOP"), ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT])]))
        return t

    story.append(Paragraph("Packaging", _SECTION))
    if s["packaging"]:
        story.append(grid(["Containers", "Quantity per container", "Unit", "Total"],
                          [[p["count"], p["quantity"], p["unit"], p["count"] * p["quantity"]] for p in s["packaging"]],
                          [0.2, 0.3, 0.2, 0.3]))
    else:
        story.append(Paragraph("No packaging recorded.", _VALUE))
    story.append(Paragraph("History", _SECTION))
    story.append(grid(["Date and time", "By", "Action"],
                      [[h["timestamp"].replace("T", " ").rstrip("Z"), h["changed_by_name"], h["action"]] for h in s["history"]],
                      [0.22, 0.16, 0.62]))
    pdf, _ = _build(story, page, f"Sample Report {s['lab_no']}", user)
    return pdf


def pdf_response(pdf_bytes, name):
    response = Response(pdf_bytes, mimetype="application/pdf")
    response.headers["Content-Disposition"] = f'attachment; filename="{name}_{datetime.now():%Y%m%d_%H%M%S}.pdf"'
    return response
