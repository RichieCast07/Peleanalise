"""
Professional PDF report generator using ReportLab.
"""

import io
import base64
from datetime import datetime
from typing import Any

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image as RLImage, HRFlowable, KeepTogether,
)


LESION_LABELS = {
    "MELANOMA": "Melanoma",
    "NEVUS": "Nevus",
    "CARCINOMA_BASOCELULAR": "Carcinoma basocelular",
    "CARCINOMA_ESPINOCELULAR": "Carcinoma espinocelular",
    "QUERATOSIS_ACTINCA": "Queratosis actínica",
    "DERMATOFIBROMA": "Dermatofibroma",
    "LESION_VASCULAR": "Lesión vascular",
    "OTRO": "Otro / sin definir",
}


def _lesion_label(value: Any) -> str:
    """Nombre legible del tipo de lesión (el guion bajo impedía que el texto se partiera bien)."""
    v = str(value or "—")
    return LESION_LABELS.get(v, v.replace("_", " ").capitalize())


BRAND_BLUE   = colors.HexColor("#4f46e5")
BRAND_GRAY   = colors.HexColor("#6b7280")
RISK_COLORS  = {
    "BENIGNO":    colors.HexColor("#10b981"),
    "SOSPECHOSO": colors.HexColor("#f59e0b"),
    "MALIGNO":    colors.HexColor("#ef4444"),
}


def generate_pdf(study_data: dict[str, Any], image_b64: dict[str, str]) -> bytes:
    buffer = io.BytesIO()
    doc    = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "Title", parent=styles["Title"],
        textColor=BRAND_BLUE, fontSize=18, spaceAfter=6,
    )
    heading_style = ParagraphStyle(
        "Heading", parent=styles["Heading2"],
        textColor=BRAND_BLUE, fontSize=12, spaceBefore=12, spaceAfter=4,
    )
    label_style = ParagraphStyle(
        "Label", parent=styles["Normal"],
        textColor=BRAND_GRAY, fontSize=8,
    )
    value_style = ParagraphStyle(
        "Value", parent=styles["Normal"],
        fontSize=10, fontName="Helvetica-Bold",
    )

    story = []

    # ── Header ──────────────────────────────────────────────────────────────
    story.append(Paragraph("PeleAnálise", title_style))
    story.append(Paragraph("Reporte de Análisis Dermatológico", styles["Normal"]))
    story.append(HRFlowable(width="100%", color=BRAND_BLUE, thickness=1.5, spaceAfter=12))

    # ── Patient info ─────────────────────────────────────────────────────────
    p = study_data.get("patient", {})
    story.append(Paragraph("Datos del Paciente", heading_style))

    patient_table_data = [
        [Paragraph("Nombre", label_style),
         Paragraph(f"{p.get('firstName','')} {p.get('lastName','')}", value_style),
         Paragraph("Fecha nacimiento", label_style),
         Paragraph(str(p.get("birthDate", "—"))[:10], value_style)],
        [Paragraph("Sexo", label_style),
         Paragraph(str(p.get("sex", "—")), value_style),
         Paragraph("CURP", label_style),
         Paragraph(str(p.get("curp") or "—"), value_style)],
    ]
    pt = Table(patient_table_data, colWidths=[3 * cm, 5.5 * cm, 3 * cm, 5.5 * cm])
    pt.setStyle(TableStyle([
        ("FONTSIZE",   (0, 0), (-1, -1), 9),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
    ]))
    story.append(pt)

    # ── Study info ──────────────────────────────────────────────────────────
    story.append(Paragraph("Datos del Estudio", heading_style))
    study_date = str(study_data.get("studyDate", ""))[:10]

    study_info = Table([
        [Paragraph("Fecha", label_style), Paragraph(study_date, value_style),
         Paragraph("Localización", label_style), Paragraph(str(study_data.get("anatomicLocation", "—")), value_style)],
        [Paragraph("Tipo de lesión", label_style), Paragraph(_lesion_label(study_data.get("lesionType")), value_style),
         Paragraph("Capturado por", label_style), Paragraph(f"{study_data.get('capturedBy', {}).get('firstName', '')} {study_data.get('capturedBy', {}).get('lastName', '')}", value_style)],
    ], colWidths=[3 * cm, 5.5 * cm, 3 * cm, 5.5 * cm])
    story.append(study_info)

    # ── Images ──────────────────────────────────────────────────────────────
    story.append(Paragraph("Imágenes del Estudio", heading_style))
    caption_style = ParagraphStyle("Caption", parent=label_style, alignment=1, leading=11)
    img_cells = []
    for img_type, b64 in image_b64.items():
        if not b64:
            continue
        try:
            img_data = base64.b64decode(b64)
            img      = RLImage(io.BytesIO(img_data), width=5 * cm, height=5 * cm)
            # Cada imagen con su etiqueta debajo, centradas entre sí
            cell = Table([[img], [Paragraph(img_type, caption_style)]], colWidths=[5.2 * cm])
            cell.setStyle(TableStyle([
                ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
                ("VALIGN",        (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING",    (0, 1), (-1, 1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            img_cells.append(cell)
        except Exception:
            pass

    if img_cells:
        # 3 columnas de 5,6 cm = 16,8 cm: caben dentro de los márgenes (ancho útil 17 cm)
        img_table = Table([img_cells[:3]], colWidths=[5.6 * cm] * min(len(img_cells), 3))
        img_table.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "TOP")]))
        story.append(img_table)

    # ── ABCDE ───────────────────────────────────────────────────────────────
    analysis = study_data.get("analysis", {})
    abcde    = analysis.get("abcde", {})
    if abcde:
        story.append(Paragraph("Análisis ABCDE", heading_style))
        rows = [
            ["Criterio", "Score", "Detalles"],
            ["A — Asimetría",  f"{abcde.get('asymmetryScore', 0):.3f}", f"H: {abcde.get('asymmetryH',0):.3f}  V: {abcde.get('asymmetryV',0):.3f}"],
            ["B — Bordes",     f"{abcde.get('borderScore', 0):.3f}",    f"Compacidad: {abcde.get('compactness',0):.3f}  Rugosidad: {abcde.get('rugosity',0):.3f}"],
            ["C — Color",      f"{abcde.get('colorScore', 0):.3f}",     f"Varianza cromática: {abcde.get('colorVariance',0):.3f}"],
            ["D — Diámetro",   f"{abcde.get('diameterMm', 0):.2f} mm",  f"Píxeles: {abcde.get('diameterPx',0):.1f}"],
            ["TOTAL",          f"{abcde.get('totalScore', 0):.3f}",     ""],
        ]
        t = Table(rows, colWidths=[5 * cm, 3 * cm, 9 * cm])
        t.setStyle(TableStyle([
            ("BACKGROUND",  (0, 0), (-1, 0), BRAND_BLUE),
            ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
            ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",    (0, 0), (-1, -1), 9),
            ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, colors.HexColor("#f9fafb")]),
            ("BACKGROUND",  (0, -1), (-1, -1), colors.HexColor("#e0e7ff")),
            ("FONTNAME",    (0, -1), (-1, -1), "Helvetica-Bold"),
            ("GRID",        (0, 0), (-1, -1), 0.5, colors.HexColor("#e5e7eb")),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]))
        story.append(t)

    # ── AI Prediction ────────────────────────────────────────────────────────
    prediction = analysis.get("prediction", {})
    # Toda la sección de predicción + pie va junta: así no se parte entre dos hojas ni se pisa con el pie.
    tail: list = []
    if prediction:
        tail.append(Paragraph("Predicción de Inteligencia Artificial", heading_style))
        risk  = str(prediction.get("prediction", "")).upper()
        color = RISK_COLORS.get(risk, BRAND_GRAY)

        # leading (interlineado) debe ser mayor que el tamaño de letra: con el valor por defecto (12)
        # las letras de 20 pt se encimaban con la línea siguiente.
        pred_style = ParagraphStyle(
            "Pred", parent=styles["Normal"],
            fontSize=20, leading=26, spaceAfter=6, fontName="Helvetica-Bold", textColor=color,
        )
        tail.append(Paragraph(str(prediction.get("prediction") or "—"), pred_style))

        model_version = str(prediction.get("modelVersion") or "—")
        is_demo       = model_version.startswith("demo")
        model_label   = (
            "Modelo de demostración" if is_demo
            else f"Modelo v{model_version}" if model_version[:1].isdigit()
            else f"Modelo {model_version}"
        )
        tail.append(Paragraph(
            f"Probabilidad: {round(float(prediction.get('probability', 0)) * 100)}% · {model_label}",
            ParagraphStyle("ProbLine", parent=styles["Normal"], fontSize=10, leading=14),
        ))
        tail.append(Spacer(1, 8))

        if is_demo:
            box_text  = ("<b>RESULTADO DE DEMOSTRACIÓN.</b> No hay un modelo de IA entrenado cargado en el sistema; "
                         "la clasificación y las probabilidades NO tienen validez clínica. "
                         "Las métricas ABCDE sí se calculan sobre la imagen.")
            box_bg, box_line, box_fg = "#fffbeb", "#fcd34d", "#92400e"
        else:
            box_text  = ("<b>Modelo experimental de apoyo.</b> Puede omitir lesiones malignas y generar falsas alarmas. "
                         "No sustituye el diagnóstico del dermatólogo ni la biopsia.")
            box_bg, box_line, box_fg = "#f0f9ff", "#bae6fd", "#075985"

        # Recuadro como tabla (no como Paragraph con borderPadding, que se sale de su caja y pisa el texto vecino)
        box = Table(
            [[Paragraph(box_text, ParagraphStyle("Box", parent=styles["Normal"], fontSize=9, leading=12,
                                                 textColor=colors.HexColor(box_fg)))]],
            colWidths=[17 * cm],
        )
        box.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor(box_bg)),
            ("BOX",           (0, 0), (-1, -1), 0.8, colors.HexColor(box_line)),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
            ("TOPPADDING",    (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        tail.append(box)

    # ── Footer ───────────────────────────────────────────────────────────────
    tail.append(Spacer(1, 0.8 * cm))
    tail.append(HRFlowable(width="100%", color=BRAND_GRAY, thickness=0.5, spaceAfter=4))
    tail.append(Paragraph(
        f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')} · PeleAnálise v1.0 · "
        "Este reporte es una herramienta de apoyo clínico. No reemplaza el juicio médico profesional.",
        ParagraphStyle("Footer", parent=styles["Normal"], fontSize=7, leading=10, textColor=BRAND_GRAY),
    ))

    story.append(KeepTogether(tail))

    doc.build(story)
    return buffer.getvalue()
