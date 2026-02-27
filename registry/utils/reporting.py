# registry/utils/reporting.py
from reportlab.lib import colors
from reportlab.platypus import HRFlowable
from io import BytesIO
import os
from django.http import HttpResponse
from django.utils.timezone import now
from django.utils.text import capfirst
from django.conf import settings
import datetime
from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    Image,
)
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics


def queryset_to_pdf(queryset, user, fields, title="", logo_path=None, summary=None, order_by=None):
    """
    Generic PDF generator for any model queryset.
    Handles:
      - Dynamic columns
      - Summary table
      - Zebra rows
      - Boolean/number alignment
      - Header styling
      - Optional logo
    """

    buffer = BytesIO()
    page_size = landscape(A4)

    # ----------------------------
    # Register Unicode fonts
    # ----------------------------
    font_regular_path = os.path.join(settings.BASE_DIR, "fonts", "DejaVuSans.ttf")
    font_bold_path = os.path.join(settings.BASE_DIR, "fonts", "DejaVuSans-Bold.ttf")
    pdfmetrics.registerFont(TTFont("DejaVuSans", font_regular_path))
    pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", font_bold_path))

    # ----------------------------
    # Document setup
    # ----------------------------
    doc = SimpleDocTemplate(
        buffer,
        pagesize=page_size,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    elements = []
    styles = getSampleStyleSheet()

    # ----------------------------
    # Table styles
    # ----------------------------
    table_header_style = styles["Normal"].clone("table_header")
    table_header_style.fontName = "DejaVuSans-Bold"
    table_header_style.fontSize = 9
    table_header_style.leading = 11

    table_cell_style = styles["Normal"].clone("table_cell")
    table_cell_style.fontName = "DejaVuSans"
    table_cell_style.fontSize = 9
    table_cell_style.leading = 11

    styles["Normal"].fontName = "DejaVuSans"
    styles["Heading1"].fontName = "DejaVuSans-Bold"
    styles["Heading2"].fontName = "DejaVuSans-Bold"

    # ----------------------------
    # Header with logo
    # ----------------------------
    if logo_path and os.path.exists(logo_path):
        logo = Image(logo_path)
        max_width, max_height = 3 * cm, 3 * cm
        ratio = min(max_width / logo.imageWidth, max_height / logo.imageHeight)
        logo.drawWidth = logo.imageWidth * ratio
        logo.drawHeight = logo.imageHeight * ratio
        logo.hAlign = "LEFT"
    else:
        logo = Paragraph("", styles["Normal"])

    title_info = [
        Paragraph(title, styles["Heading1"]),
        Spacer(1, 0.1 * cm),
        #Paragraph(f"Izradio: {user.username}", styles["Normal"]),
        Paragraph(f"Datum i vrijme: {now().strftime('%d-%m-%Y %H:%M')}", styles["Normal"]),
    ]

    header_table = Table([[logo, title_info]], colWidths=[3.5 * cm, 18 * cm])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    elements.append(header_table)
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    elements.append(Spacer(1, 0.5 * cm))

    # ----------------------------
    # Summary table (optional)
    # ----------------------------
    if summary:
        summary_data = [
            ["Ukupno obrta", summary['total_businesses']],
            ["Aktivnih", summary['active_businesses']],
            ["Neaktivnih", summary['inactive_businesses']],
            ["PDV obveznika", summary['vat_registered']],
            ["Ukupno zaposlenih", summary['total_employees']],
            ["Prosjek zaposlenih", f"{summary['avg_employees']:.2f}"]
        ]
        summary_table = Table(summary_data, colWidths=[8*cm, 4*cm])
        summary_table.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
            ("BOX", (0,0), (-1,-1), 1, colors.grey),
            ("INNERGRID", (0,0), (-1,-1), 0.5, colors.grey),
            ("ALIGN", (1,0), (1,-1), "RIGHT"),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("LEFTPADDING", (0,0), (-1,-1), 4),
            ("RIGHTPADDING", (0,0), (-1,-1), 4),
            ("TOPPADDING", (0,0), (-1,-1), 4),
            ("BOTTOMPADDING", (0,0), (-1,-1), 4),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 1*cm))

    # ----------------------------
    # Table data
    # ----------------------------
    if order_by:
        queryset = queryset.order_by(order_by)

    model = queryset.model
    headers = [Paragraph(capfirst(model._meta.get_field(f).verbose_name), table_header_style)
               for f in fields]
    data = [headers]

    for obj in queryset:
        row = []
        for field in fields:
            value = getattr(obj, field, "")
            display_method = f"get_{field}_display"
            if hasattr(obj, display_method):
                value = getattr(obj, display_method)()
            if value is None:
                value = ""
            elif isinstance(value, bool):
                value = "Da" if value else "Ne"
            elif isinstance(value, (datetime.date, datetime.datetime)):
                value = value.strftime("%d.%m.%Y.")
                
            row.append(Paragraph(str(value), table_cell_style))
        data.append(row)

    # ----------------------------
    # Table creation with dynamic widths
    # ----------------------------
    available_width = page_size[0] - 4 * cm
    col_widths = [available_width / len(fields)] * len(fields)

    table = Table(data, repeatRows=1, colWidths=col_widths)
    table_style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("FONTNAME", (0, 0), (-1, 0), "DejaVuSans-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ])

    # Zebra striping
    for i in range(1, len(data)):
        if i % 2 == 0:
            table_style.add("BACKGROUND", (0, i), (-1, i), colors.whitesmoke)

    # Column alignment
    for col_idx, field in enumerate(fields):
        is_boolean = False
        is_numeric = False
        for obj in queryset:
            value = getattr(obj, field, None)
            if hasattr(obj, f"get_{field}_display"):
                value = getattr(obj, f"get_{field}_display")()
            if isinstance(value, bool):
                is_boolean = True
                break
            elif isinstance(value, (int, float)):
                is_numeric = True
                break
        if is_boolean:
            table_style.add("ALIGN", (col_idx, 1), (col_idx, -1), "CENTER")
        elif is_numeric:
            table_style.add("ALIGN", (col_idx, 1), (col_idx, -1), "RIGHT")

    table.setStyle(table_style)
    elements.append(table)

    # ----------------------------
    # Page numbers
    # ----------------------------
    def add_page_number(canvas, doc):
        canvas.setFont("DejaVuSans", 8)
        canvas.drawRightString(page_size[0] - 2 * cm, 1.5 * cm, f"Strana {doc.page}")
        canvas.drawString(2 * cm, 1.5 * cm, f"Izradio: {user.username}")

    doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)

    buffer.seek(0)
    response = HttpResponse(buffer, content_type="application/pdf")
    response["Content-Disposition"] = f"inline; filename={model.__name__}_report.pdf"
    return response