from io import BytesIO
from django.http import HttpResponse
from django.utils.timezone import now

from reportlab.platypus import (
    SimpleDocTemplate,
    Table,
    TableStyle,
    Paragraph,
    Spacer
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics


def businesses_to_pdf(queryset, user):
    buffer = BytesIO()

    # Landscape A4
    page_size = landscape(A4)

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

    # ---------------------------------------------------
    # HEADER
    # ---------------------------------------------------

    title_style = styles["Heading1"]
    subtitle_style = styles["Normal"]

    elements.append(Paragraph("Registar obrta Grada Goražda", title_style))
    elements.append(Spacer(1, 0.3 * cm))

    elements.append(
        Paragraph(
            f"Izvještaj obrta",
            styles["Heading2"]
        )
    )
    elements.append(Spacer(1, 0.3 * cm))

    elements.append(
        Paragraph(
            f"Generisao: {user.username}",
            subtitle_style
        )
    )
    elements.append(
        Paragraph(
            f"Datum i vrijeme: {now().strftime('%d-%m-%Y %H:%M')}",
            subtitle_style
        )
    )

    elements.append(Spacer(1, 1 * cm))

    # ---------------------------------------------------
    # TABLE DATA
    # ---------------------------------------------------

    data = [
        [
            "Name",
            "Reg. No",
            "City",
            "Status",
            "Industry",
            "Employees",
            "VAT"
        ]
    ]

    for b in queryset:
        data.append([
            b.name,
            b.registration_number,
            b.city or "",
            b.status,
            b.industry or "",
            b.number_of_employees if b.number_of_employees else "",
            "Yes" if b.is_vat_registered else "No",
        ])

    table = Table(
        data,
        repeatRows=1,  # Header repeats on every page
        colWidths=[
            6 * cm,
            3.5 * cm,
            3 * cm,
            3 * cm,
            3 * cm,
            2.5 * cm,
            2 * cm,
        ]
    )

    table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN", (5, 1), (6, -1), "CENTER"),
        ])
    )

    elements.append(table)

    # ---------------------------------------------------
    # PAGE NUMBER FUNCTION
    # ---------------------------------------------------

    def add_page_number(canvas, doc):
        page_num_text = f"Page {doc.page}"
        canvas.setFont("Helvetica", 8)
        canvas.drawRightString(
            page_size[0] - 2 * cm,
            1.5 * cm,
            page_num_text
        )

    # Build document
    doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)

    buffer.seek(0)
    response = HttpResponse(buffer, content_type="application/pdf")
    response["Content-Disposition"] = "inline; filename=businesses_report.pdf"
    return response