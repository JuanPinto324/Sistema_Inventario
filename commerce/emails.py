import io
import logging
import threading
from html import escape

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from .models import User


logger = logging.getLogger(__name__)

BRAND_NAME = "Agroveterinaria Planeta Animal"
BRAND_SUBTITLE = "Salud animal y cuidado agropecuario"
BRAND_GREEN = "#144115"
ACCENT_GREEN = "#39701B"


def _money(value):
    return f"$ {value:,.0f}".replace(",", ".")


def _destinatarios_staff():
    return list(
        User.objects.filter(
            is_active=True,
            role__in=[User.ROLE_JEFE, User.ROLE_ADMIN],
        )
        .exclude(email="")
        .values_list("email", flat=True)
    )


def _generar_pdf_factura(sale):
    """Genera el comprobante de venta en PDF y retorna sus bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=1.7 * cm,
        bottomMargin=1.7 * cm,
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "brand_title",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor(BRAND_GREEN),
    )
    subtitle_style = ParagraphStyle(
        "brand_subtitle",
        parent=styles["Normal"],
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#526173"),
    )
    document_title_style = ParagraphStyle(
        "document_title",
        parent=styles["Normal"],
        alignment=TA_RIGHT,
        fontName="Helvetica-Bold",
        fontSize=13,
        textColor=colors.HexColor(BRAND_GREEN),
    )
    document_number_style = ParagraphStyle(
        "document_number",
        parent=styles["Normal"],
        alignment=TA_RIGHT,
        fontName="Helvetica-Bold",
        fontSize=10,
        textColor=colors.HexColor("#39701B"),
    )
    section_style = ParagraphStyle(
        "section",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor(BRAND_GREEN),
        spaceAfter=5,
    )
    normal_style = ParagraphStyle(
        "normal",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1F2937"),
    )
    small_style = ParagraphStyle(
        "small",
        parent=styles["Normal"],
        alignment=TA_CENTER,
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#64748B"),
    )
    total_label_style = ParagraphStyle(
        "total_label",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        textColor=colors.white,
    )
    total_value_style = ParagraphStyle(
        "total_value",
        parent=styles["Normal"],
        alignment=TA_RIGHT,
        fontName="Helvetica-Bold",
        fontSize=15,
        textColor=colors.white,
    )

    items = list(sale.items.select_related("product").all())
    fecha = timezone.localtime(sale.created_at).strftime("%d/%m/%Y %H:%M")
    elements = []

    header = Table(
        [[
            [
                Paragraph(BRAND_NAME, title_style),
                Paragraph(BRAND_SUBTITLE, subtitle_style),
            ],
            [
                Paragraph("COMPROBANTE DE VENTA", document_title_style),
                Paragraph(escape(sale.invoice_number), document_number_style),
            ],
        ]],
        colWidths=[10.5 * cm, 6.5 * cm],
    )
    header.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    elements.append(header)
    elements.append(Spacer(1, 0.35 * cm))
    elements.append(
        HRFlowable(width="100%", thickness=2, color=colors.HexColor(ACCENT_GREEN))
    )
    elements.append(Spacer(1, 0.35 * cm))

    sale_info = [
        [Paragraph("<b>Fecha</b>", normal_style), Paragraph(escape(fecha), normal_style)],
        [Paragraph("<b>Cajero</b>", normal_style), Paragraph(escape(sale.cashier.full_name), normal_style)],
    ]
    customer_info = [
        [Paragraph("<b>Cliente</b>", normal_style), Paragraph(escape(sale.customer_name), normal_style)],
        [Paragraph("<b>Identificación</b>", normal_style), Paragraph(escape(sale.customer_id), normal_style)],
    ]
    if sale.customer_phone:
        customer_info.append(
            [Paragraph("<b>Teléfono</b>", normal_style), Paragraph(escape(sale.customer_phone), normal_style)]
        )
    if sale.customer_email:
        customer_info.append(
            [Paragraph("<b>Correo</b>", normal_style), Paragraph(escape(sale.customer_email), normal_style)]
        )

    info_table = Table(
        [[
            [Paragraph("DATOS DE LA VENTA", section_style), Table(sale_info, colWidths=[3 * cm, 5 * cm])],
            [Paragraph("DATOS DEL CLIENTE", section_style), Table(customer_info, colWidths=[3 * cm, 5 * cm])],
        ]],
        colWidths=[8.4 * cm, 8.6 * cm],
    )
    info_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#EEF5EC")),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#DCE8D9")),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#DCE8D9")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("PADDING", (0, 0), (-1, -1), 11),
            ]
        )
    )
    elements.append(info_table)
    elements.append(Spacer(1, 0.45 * cm))

    elements.append(Paragraph("PRODUCTOS", section_style))
    item_rows = [["Producto", "Cant.", "Precio unitario", "Subtotal"]]
    for item in items:
        item_rows.append(
            [
                Paragraph(escape(item.product.name), normal_style),
                str(item.quantity),
                _money(item.unit_price),
                _money(item.subtotal),
            ]
        )

    items_table = Table(
        item_rows,
        colWidths=[8.3 * cm, 2 * cm, 3.3 * cm, 3.4 * cm],
        repeatRows=1,
    )
    items_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor(BRAND_GREEN)),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (1, 0), (-1, -1), "RIGHT"),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#DCE8D9")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FBF7")]),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    elements.append(items_table)
    elements.append(Spacer(1, 0.4 * cm))

    total_table = Table(
        [[Paragraph("TOTAL PAGADO", total_label_style), Paragraph(_money(sale.total), total_value_style)]],
        colWidths=[11.5 * cm, 5.5 * cm],
    )
    total_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor(BRAND_GREEN)),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("PADDING", (0, 0), (-1, -1), 12),
            ]
        )
    )
    elements.append(total_table)
    elements.append(Spacer(1, 0.55 * cm))
    elements.append(
        Paragraph(
            "Gracias por confiar en Planeta Animal. Conserva este comprobante para cualquier consulta.",
            small_style,
        )
    )

    doc.build(elements)
    buffer.seek(0)
    return buffer.read()


def _enviar_async(subject, html_content, text_content, recipient_list, pdf_bytes=None, pdf_filename=None):
    """Envía correo en un hilo para no bloquear la venta."""
    recipient_list = [email for email in recipient_list if email]
    if not recipient_list:
        logger.warning("Correo no enviado sin destinatarios: %s", subject)
        return
    if not settings.DEFAULT_FROM_EMAIL:
        logger.error("Correo no enviado sin DEFAULT_FROM_EMAIL configurado: %s", subject)
        return

    def send():
        try:
            message = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipient_list,
            )
            message.attach_alternative(html_content, "text/html")
            if pdf_bytes and pdf_filename:
                message.attach(pdf_filename, pdf_bytes, "application/pdf")
            message.send(fail_silently=False)
        except Exception:
            logger.exception("Error enviando correo: %s", subject)

    threading.Thread(target=send, daemon=True, name="email-sender").start()


def _email_shell(title, subtitle, accent, content):
    return f"""<!DOCTYPE html>
<html lang="es">
<head><meta charset="UTF-8"></head>
<body style="margin:0;padding:0;background:#f4f8f2;font-family:Arial,sans-serif">
  <table width="100%" cellpadding="0" cellspacing="0" style="padding:32px 12px;background:#f4f8f2">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="max-width:600px;background:#ffffff;border:1px solid #dce8d9;border-radius:14px;overflow:hidden">
        <tr>
          <td style="padding:28px 32px;background:{accent};text-align:center">
            <h1 style="margin:0;color:#ffffff;font-size:22px">{title}</h1>
            <p style="margin:6px 0 0;color:#e3f0da;font-size:12px">{subtitle}</p>
          </td>
        </tr>
        {content}
        <tr>
          <td style="padding:18px 32px;background:#f8fbf7;border-top:1px solid #dce8d9;text-align:center">
            <p style="margin:0;color:#64748b;font-size:12px">Mensaje automático de {BRAND_NAME}.</p>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>
</body>
</html>"""


def enviar_confirmacion_compra(sale):
    if not sale.customer_email:
        return

    items = list(sale.items.select_related("product").all())
    fecha = timezone.localtime(sale.created_at).strftime("%d/%m/%Y %H:%M")

    rows_html = "".join(
        f"""<tr>
          <td style="padding:10px 12px;border-bottom:1px solid #dce8d9;color:#1f2937">{escape(item.product.name)}</td>
          <td style="padding:10px 12px;border-bottom:1px solid #dce8d9;text-align:center">{item.quantity}</td>
          <td style="padding:10px 12px;border-bottom:1px solid #dce8d9;text-align:right">{_money(item.unit_price)}</td>
          <td style="padding:10px 12px;border-bottom:1px solid #dce8d9;text-align:right;font-weight:bold">{_money(item.subtotal)}</td>
        </tr>"""
        for item in items
    )

    content = f"""
<tr><td style="padding:28px 32px 8px">
  <h2 style="margin:0;color:#144115;font-size:19px">Gracias por tu compra, {escape(sale.customer_name)}.</h2>
  <p style="margin:8px 0 0;color:#526173;font-size:14px;line-height:1.5">Adjuntamos tu comprobante de venta en PDF.</p>
</td></tr>
<tr><td style="padding:16px 32px">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#eef5ec;border-left:4px solid #39701b">
    <tr><td style="padding:14px 16px;color:#526173;font-size:13px">Comprobante</td><td style="padding:14px 16px;text-align:right;color:#144115;font-size:13px;font-weight:bold">{escape(sale.invoice_number)}</td></tr>
    <tr><td style="padding:0 16px 14px;color:#526173;font-size:13px">Fecha</td><td style="padding:0 16px 14px;text-align:right;color:#1f2937;font-size:13px">{escape(fecha)}</td></tr>
  </table>
</td></tr>
<tr><td style="padding:4px 32px 0">
  <h3 style="margin:0 0 10px;color:#144115;font-size:13px;letter-spacing:.04em">PRODUCTOS</h3>
  <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #dce8d9">
    <tr style="background:#144115">
      <th style="padding:10px 12px;color:#ffffff;font-size:12px;text-align:left">Producto</th>
      <th style="padding:10px 12px;color:#ffffff;font-size:12px;text-align:center">Cant.</th>
      <th style="padding:10px 12px;color:#ffffff;font-size:12px;text-align:right">Precio</th>
      <th style="padding:10px 12px;color:#ffffff;font-size:12px;text-align:right">Subtotal</th>
    </tr>
    {rows_html}
  </table>
</td></tr>
<tr><td style="padding:20px 32px 28px">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#144115">
    <tr><td style="padding:15px 16px;color:#ffffff;font-size:14px;font-weight:bold">TOTAL PAGADO</td><td style="padding:15px 16px;color:#ffffff;font-size:21px;font-weight:bold;text-align:right">{_money(sale.total)}</td></tr>
  </table>
</td></tr>"""

    html_content = _email_shell(BRAND_NAME, "Confirmación de compra", BRAND_GREEN, content)
    items_text = "\n".join(
        f"- {item.product.name} x{item.quantity}: {_money(item.subtotal)}"
        for item in items
    )
    text_content = f"""Gracias por tu compra, {sale.customer_name}.

Comprobante: {sale.invoice_number}
Fecha: {fecha}

Productos:
{items_text}

Total pagado: {_money(sale.total)}

{BRAND_NAME}
{BRAND_SUBTITLE}"""

    _enviar_async(
        subject=f"Confirmación de compra {sale.invoice_number} - Planeta Animal",
        html_content=html_content,
        text_content=text_content,
        recipient_list=[sale.customer_email],
        pdf_bytes=_generar_pdf_factura(sale),
        pdf_filename=f"Comprobante_{sale.invoice_number}.pdf",
    )


def enviar_alerta_stock_bajo(product):
    destinatarios = _destinatarios_staff()
    if not destinatarios:
        return

    content = f"""
<tr><td style="padding:28px 32px">
  <p style="margin:0 0 18px;color:#334155;font-size:14px;line-height:1.5">Este producto alcanzó el stock mínimo configurado. Programa su reposición.</p>
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#fffbeb;border-left:4px solid #b7791f">
    <tr><td style="padding:14px 16px;color:#64748b;font-size:13px">Producto</td><td style="padding:14px 16px;text-align:right;color:#1f2937;font-weight:bold;font-size:13px">{escape(product.name)}</td></tr>
    <tr><td style="padding:0 16px 14px;color:#64748b;font-size:13px">Código</td><td style="padding:0 16px 14px;text-align:right;color:#1f2937;font-size:13px">{escape(product.code)}</td></tr>
    <tr><td style="padding:0 16px 14px;color:#64748b;font-size:13px">Stock actual</td><td style="padding:0 16px 14px;text-align:right;color:#b7791f;font-weight:bold;font-size:13px">{product.stock} unidades</td></tr>
    <tr><td style="padding:0 16px 14px;color:#64748b;font-size:13px">Stock mínimo</td><td style="padding:0 16px 14px;text-align:right;color:#1f2937;font-size:13px">{product.min_stock} unidades</td></tr>
  </table>
</td></tr>"""

    _enviar_async(
        subject=f"Stock bajo: {product.name} - Planeta Animal",
        html_content=_email_shell(BRAND_NAME, "Alerta de stock bajo", "#B7791F", content),
        text_content=f"""Alerta de stock bajo

Producto: {product.name}
Código: {product.code}
Stock actual: {product.stock} unidades
Stock mínimo: {product.min_stock} unidades

Programa su reposición.
{BRAND_NAME}""",
        recipient_list=destinatarios,
    )


def enviar_alerta_stock_agotado(product):
    destinatarios = _destinatarios_staff()
    if not destinatarios:
        return

    fecha = timezone.localtime(timezone.now()).strftime("%d/%m/%Y %H:%M")
    content = f"""
<tr><td style="padding:28px 32px">
  <p style="margin:0 0 18px;color:#334155;font-size:14px;line-height:1.5">Este producto se agotó. Reabastécelo para evitar perder ventas.</p>
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#fef2f2;border-left:4px solid #dc2626">
    <tr><td style="padding:14px 16px;color:#64748b;font-size:13px">Producto</td><td style="padding:14px 16px;text-align:right;color:#1f2937;font-weight:bold;font-size:13px">{escape(product.name)}</td></tr>
    <tr><td style="padding:0 16px 14px;color:#64748b;font-size:13px">Código</td><td style="padding:0 16px 14px;text-align:right;color:#1f2937;font-size:13px">{escape(product.code)}</td></tr>
    <tr><td style="padding:0 16px 14px;color:#64748b;font-size:13px">Stock actual</td><td style="padding:0 16px 14px;text-align:right;color:#dc2626;font-weight:bold;font-size:13px">0 unidades</td></tr>
    <tr><td style="padding:0 16px 14px;color:#64748b;font-size:13px">Fecha</td><td style="padding:0 16px 14px;text-align:right;color:#1f2937;font-size:13px">{escape(fecha)}</td></tr>
  </table>
</td></tr>"""

    _enviar_async(
        subject=f"Producto agotado: {product.name} - Planeta Animal",
        html_content=_email_shell(BRAND_NAME, "Alerta de producto agotado", "#DC2626", content),
        text_content=f"""Producto agotado

Producto: {product.name}
Código: {product.code}
Stock actual: 0 unidades
Fecha: {fecha}

Se requiere reposición urgente.
{BRAND_NAME}""",
        recipient_list=destinatarios,
    )