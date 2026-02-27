#pdf.py
from io import BytesIO
import os
import datetime
from django.http import HttpResponse
from django.utils.timezone import now
from django.utils.text import capfirst
from django.conf import settings

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer,
    HRFlowable,
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics


def businesses_to_pdf(queryset, user, order_by="name"):
    """
    Generates a professional PDF report for businesses.
    """

    buffer = BytesIO()
    page_size = landscape(A4)

    # =====================================================
    # REGISTER UNICODE FONTS (Č Ć Š Ž Đ SUPPORT)
    # =====================================================

    font_regular_path = os.path.join(settings.BASE_DIR, "fonts", "DejaVuSans.ttf")
    font_bold_path = os.path.join(settings.BASE_DIR, "fonts", "DejaVuSans-Bold.ttf")

    pdfmetrics.registerFont(TTFont("DejaVuSans", font_regular_path))
    pdfmetrics.registerFont(TTFont("DejaVuSans-Bold", font_bold_path))

    # =====================================================
    # DOCUMENT SETUP
    # =====================================================

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

    # Apply Unicode fonts
    styles["Normal"].fontName = "DejaVuSans"
    styles["Heading1"].fontName = "DejaVuSans-Bold"
    styles["Heading2"].fontName = "DejaVuSans-Bold"

    # Table styles
    table_header_style = styles["Normal"].clone("table_header")
    table_header_style.fontName = "DejaVuSans-Bold"
    table_header_style.fontSize = 9
    table_header_style.leading = 11

    table_cell_style = styles["Normal"].clone("table_cell")
    table_cell_style.fontName = "DejaVuSans"
    table_cell_style.fontSize = 9
    table_cell_style.leading = 11

    # =====================================================
    # ORDER DATA
    # =====================================================

    queryset = queryset.order_by(order_by)

    # =====================================================
    # HEADER SECTION
    # =====================================================

    elements.append(Paragraph("<b>REGISTAR OBRTA GRADA GORAŽDA</b>", styles["Heading1"]))
    elements.append(Spacer(1, 0.2 * cm))
    elements.append(Paragraph("Službeni izvještaj", styles["Normal"]))
    elements.append(Spacer(1, 0.3 * cm))
    elements.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    elements.append(Spacer(1, 0.5 * cm))

    elements.append(Paragraph("Informacije o izvještaju", styles["Heading2"]))
    elements.append(Spacer(1, 0.2 * cm))
    elements.append(Paragraph(f"Generisao: {user.username}", styles["Normal"]))
    elements.append(
        Paragraph(
            f"Datum i vrijeme: {now().strftime('%d-%m-%Y %H:%M')}",
            styles["Normal"],
        )
    )
    elements.append(Spacer(1, 0.8 * cm))

    # =====================================================
    # SUMMARY SECTION
    # =====================================================

    elements.append(Paragraph("Sažetak", styles["Heading2"]))
    elements.append(Spacer(1, 0.3 * cm))

    total = queryset.count()
    active = queryset.filter(status="active").count()

    summary_data = [
        ["Ukupan broj obrta:", str(total)],
        ["Aktivni obrti:", str(active)],
    ]

    summary_table = Table(summary_data, colWidths=[6 * cm, 3 * cm])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.whitesmoke),
        ("BOX", (0, 0), (-1, -1), 1, colors.grey),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))

    elements.append(summary_table)
    elements.append(Spacer(1, 1 * cm))

    # =====================================================
    # TABLE DATA
    # =====================================================

    model = queryset.model
    fields = [
        "name",
        "registration_number",
        "city",
        "status",
        "industry",
        "number_of_employees",
        "is_vat_registered",
        "activity_code",
    ]

    headers = [
        Paragraph(capfirst(model._meta.get_field(field).verbose_name), table_header_style)
        for field in fields
    ]

    data = [headers]

    for obj in queryset.iterator():  # memory safe
        row = []
        for field in fields:
            display_method = f"get_{field}_display"
            if hasattr(obj, display_method):
                value = getattr(obj, display_method)()
            else:
                value = getattr(obj, field)

            if value is None:
                value = ""
            elif isinstance(value, bool):
                value = "Da" if value else "Ne"
            elif isinstance(value, (datetime.date, datetime.datetime)):
                value = value.strftime("%d.%m.%Y.")
                
            row.append(Paragraph(str(value), table_cell_style))

        data.append(row)

    # =====================================================
    # TABLE CREATION
    # =====================================================

    available_width = page_size[0] - (4 * cm)
    col_width = available_width / len(fields)

    table = Table(
        data,
        repeatRows=1,
        colWidths=[col_width] * len(fields),
    )

    table_style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (5, 1), (6, -1), "CENTER"),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ])

    # Zebra striping
    for i in range(1, len(data)):
        if i % 2 == 0:
            table_style.add("BACKGROUND", (0, i), (-1, i), colors.whitesmoke)

    table.setStyle(table_style)

    elements.append(table)

    # =====================================================
    # FOOTER (PAGE NUMBER + USER)
    # =====================================================

    def add_page_number(canvas, doc):
        canvas.setFont("DejaVuSans", 8)

        canvas.drawRightString(
            page_size[0] - 2 * cm,
            1.2 * cm,
            f"Stranica {doc.page}",
        )

        canvas.drawString(
            2 * cm,
            1.2 * cm,
            f"Izvještaj generisan od: {user.username}",
        )

    doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)

    buffer.seek(0)
    response = HttpResponse(buffer, content_type="application/pdf")
    response["Content-Disposition"] = "inline; filename=businesses_report.pdf"

    return response