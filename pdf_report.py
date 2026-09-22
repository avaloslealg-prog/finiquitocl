from io import BytesIO
from datetime import date

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle

from calculo import Resultado, CAUSALES


def _clp(n: int) -> str:
    return f"${n:,.0f}".replace(",", ".")


def generar_pdf(
    resultado: Resultado,
    nombre: str,
    causal: str,
    ingreso: date,
    termino: date,
    valor_uf: float,
) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        leftMargin=1.8 * cm,
        rightMargin=1.8 * cm,
        topMargin=1.6 * cm,
        bottomMargin=1.6 * cm,
    )
    styles = getSampleStyleSheet()
    title = ParagraphStyle(
        "T",
        parent=styles["Heading1"],
        fontSize=18,
        textColor=colors.HexColor("#0f3d2e"),
        spaceAfter=6,
    )
    sub = ParagraphStyle(
        "S",
        parent=styles["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#4a5c55"),
        spaceAfter=12,
    )
    body = ParagraphStyle("B", parent=styles["Normal"], fontSize=10, leading=14)

    story = [
        Paragraph("FiniquitoCL — Estimación de finiquito", title),
        Paragraph(
            f"Documento referencial · {date.today().strftime('%d-%m-%Y')} · UF ${valor_uf:,.2f}".replace(",", "."),
            sub,
        ),
        Paragraph(f"<b>Trabajador / caso:</b> {nombre or 'No informado'}", body),
        Paragraph(f"<b>Causal:</b> {CAUSALES.get(causal, causal)}", body),
        Paragraph(
            f"<b>Ingreso:</b> {ingreso.strftime('%d-%m-%Y')} &nbsp;&nbsp; "
            f"<b>Término:</b> {termino.strftime('%d-%m-%Y')} &nbsp;&nbsp; "
            f"<b>Antigüedad:</b> {resultado.anos_exactos} años y {resultado.meses_fraccion} meses",
            body,
        ),
        Spacer(1, 12),
    ]

    data = [
        ["Concepto", "Detalle", "Monto"],
        [
            "Sueldo proporcional del mes",
            f"{resultado.dias_mes} días × (remuneración / 30)",
            _clp(resultado.sueldo_proporcional),
        ],
        [
            "Feriado proporcional + pendiente",
            f"{resultado.feriado_total_dias:.2f} días "
            f"({resultado.feriado_prop_dias:.2f} prop. + {resultado.feriado_pend_dias:.2f} pend.)",
            _clp(resultado.feriado),
        ],
        [
            "Indemnización años de servicio",
            f"{resultado.anos_indemnizables} año(s) × {_clp(resultado.remuneracion_topeada)}"
            if resultado.aplica_ias
            else "No aplica para esta causal",
            _clp(resultado.ias),
        ],
        [
            "Indemnización sustitutiva aviso previo",
            "30 días (sin aviso)" if resultado.aplica_aviso else "No aplica",
            _clp(resultado.aviso),
        ],
        ["TOTAL ESTIMADO", "", _clp(resultado.total)],
    ]

    table = Table(data, colWidths=[6.2 * cm, 7.2 * cm, 4 * cm])
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f3d2e")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("BACKGROUND", (0, -1), (-1, -1), colors.HexColor("#e8f5ef")),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (2, 0), (2, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#c5d5cc")),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]
        )
    )
    story.append(table)
    story.append(Spacer(1, 14))
    story.append(Paragraph("<b>Notas</b>", body))
    for n in resultado.notas:
        story.append(Paragraph(f"• {n}", body))
    story.append(Spacer(1, 10))
    story.append(
        Paragraph(
            "Este PDF es una estimación. Verifica el caso concreto con la Dirección del Trabajo "
            "o un abogado laboral antes de firmar un finiquito.",
            sub,
        )
    )
    doc.build(story)
    return buf.getvalue()
