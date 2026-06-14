import threading
import io
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.utils import timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from .models import User


def _destinatarios_staff():
    return list(
        User.objects.filter(
            is_active=True,
            role__in=[User.ROLE_JEFE, User.ROLE_ADMIN],
        ).exclude(email="").values_list("email", flat=True)
    )


def _generar_pdf_factura(sale):
    """Genera el PDF de la factura y retorna los bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=2*cm,
        leftMargin=2*cm,
        topMargin=2*cm,
        bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()
    estilo_center = ParagraphStyle('center', parent=styles['Normal'], alignment=TA_CENTER)
    estilo_right = ParagraphStyle('right', parent=styles['Normal'], alignment=TA_RIGHT)
    estilo_titulo = ParagraphStyle('titulo', parent=styles['Normal'], alignment=TA_CENTER, fontSize=16, fontName='Helvetica-Bold')
    estilo_subtitulo = ParagraphStyle('subtitulo', parent=styles['Normal'], alignment=TA_CENTER, fontSize=9, textColor=colors.grey)
    estilo_seccion = ParagraphStyle('seccion', parent=styles['Normal'], fontSize=9, fontName='Helvetica-Bold')
    estilo_normal = ParagraphStyle('normal', parent=styles['Normal'], fontSize=9)
    estilo_total = ParagraphStyle('total', parent=styles['Normal'], fontSize=13, fontName='Helvetica-Bold')

    fecha = timezone.localtime(sale.created_at).strftime('%d/%m/%Y %H:%M')
    elementos = []

    # Encabezado
    elementos.append(Paragraph("PyCommerceX", estilo_titulo))
    elementos.append(Paragraph("Sistema de Gestión Comercial", estilo_subtitulo))
    elementos.append(Spacer(1, 0.4*cm))
    elementos.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
    elementos.append(Spacer(1, 0.3*cm))

    # Info factura
    info_factura = [
        ["Factura:", sale.invoice_number],
        ["Fecha:", fecha],
        ["Cajero:", sale.cashier.full_name],
    ]
    tabla_info = Table(info_factura, colWidths=[4*cm, 13*cm])
    tabla_info.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elementos.append(tabla_info)
    elementos.append(Spacer(1, 0.3*cm))
    elementos.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    elementos.append(Spacer(1, 0.3*cm))

    # Info cliente
    info_cliente = [["Cliente:", sale.customer_name], ["ID:", sale.customer_id]]
    if sale.customer_phone:
        info_cliente.append(["Tel:", sale.customer_phone])
    if sale.customer_email:
        info_cliente.append(["Email:", sale.customer_email])
    tabla_cliente = Table(info_cliente, colWidths=[4*cm, 13*cm])
    tabla_cliente.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))
    elementos.append(tabla_cliente)
    elementos.append(Spacer(1, 0.3*cm))
    elementos.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    elementos.append(Spacer(1, 0.3*cm))

    # Artículos
    elementos.append(Paragraph("ARTÍCULOS", estilo_seccion))
    elementos.append(Spacer(1, 0.2*cm))

    datos_items = [["Producto", "Cant.", "P. Unit.", "Subtotal"]]
    for item in sale.items.all():
        datos_items.append([
            item.product.name,
            str(item.quantity),
            f"$ {item.unit_price:,}".replace(",", "."),
            f"$ {item.subtotal:,}".replace(",", "."),
        ])

    tabla_items = Table(datos_items, colWidths=[9*cm, 2*cm, 3*cm, 3*cm])
    tabla_items.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f5f5f5')),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
        ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
        ('GRID', (0, 0), (-1, -1), 0.3, colors.lightgrey),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
    ]))
    elementos.append(tabla_items)
    elementos.append(Spacer(1, 0.4*cm))
    elementos.append(HRFlowable(width="100%", thickness=1, color=colors.lightgrey))
    elementos.append(Spacer(1, 0.3*cm))

    # Total
    total_str = f"$ {sale.total:,}".replace(",", ".")
    tabla_total = Table([["TOTAL", total_str]], colWidths=[14*cm, 3*cm])
    tabla_total.setStyle(TableStyle([
        ('FONTSIZE', (0, 0), (-1, -1), 13),
        ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
    ]))
    elementos.append(tabla_total)
    elementos.append(Spacer(1, 0.5*cm))
    elementos.append(HRFlowable(width="100%", thickness=0.5, color=colors.lightgrey))
    elementos.append(Spacer(1, 0.3*cm))
    elementos.append(Paragraph("Gracias por su compra.", estilo_center))

    doc.build(elementos)
    buffer.seek(0)
    return buffer.read()


def _enviar_async(subject, html_content, text_content, recipient_list, pdf_bytes=None, pdf_filename=None):
    """Envía el correo en un hilo separado para no bloquear la petición."""
    def _send():
        try:
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipient_list,
            )
            msg.attach_alternative(html_content, "text/html")
            if pdf_bytes and pdf_filename:
                msg.attach(pdf_filename, pdf_bytes, "application/pdf")
            msg.send(fail_silently=True)
        except Exception:
            pass
    threading.Thread(target=_send, daemon=True).start()


def enviar_confirmacion_compra(sale):
    if not sale.customer_email:
        return

    fecha = timezone.localtime(sale.created_at).strftime('%d/%m/%Y %H:%M')

    items_html = "".join(f"""
        <tr>
            <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0">{item.product.name}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0;text-align:center">{item.quantity}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0;text-align:right">$ {item.unit_price:,}</td>
            <td style="padding:8px 12px;border-bottom:1px solid #f0f0f0;text-align:right">$ {item.subtotal:,}</td>
        </tr>
    """ for item in sale.items.all())

    items_texto = "\n".join(
        f"  - {item.product.name} x{item.quantity} = $ {item.subtotal:,}"
        for item in sale.items.all()
    )

    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="margin:0;padding:0;background:#f4f4f4;font-family:Arial,sans-serif">
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f4;padding:30px 0">
            <tr><td align="center">
                <table width="580" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08)">

                    <!-- Header -->
                    <tr>
                        <td style="background:#1a1a2e;padding:30px;text-align:center">
                            <h1 style="margin:0;color:#ffffff;font-size:24px;letter-spacing:1px">PyCommerceX</h1>
                            <p style="margin:4px 0 0;color:#aaaacc;font-size:12px">Sistema de Gestión Comercial</p>
                        </td>
                    </tr>

                    <!-- Saludo -->
                    <tr>
                        <td style="padding:28px 30px 0">
                            <h2 style="margin:0;color:#1a1a2e;font-size:18px">¡Gracias por tu compra, {sale.customer_name}!</h2>
                            <p style="color:#666;font-size:14px;margin:8px 0 0">Tu compra ha sido registrada exitosamente. Encuentra el comprobante adjunto a este correo.</p>
                        </td>
                    </tr>

                    <!-- Info factura -->
                    <tr>
                        <td style="padding:20px 30px">
                            <table width="100%" cellpadding="0" cellspacing="0" style="background:#f8f9ff;border-radius:6px;border-left:4px solid #1a1a2e">
                                <tr>
                                    <td style="padding:16px 20px">
                                        <table width="100%">
                                            <tr>
                                                <td style="color:#666;font-size:13px;padding:3px 0">Factura</td>
                                                <td style="color:#1a1a2e;font-size:13px;font-weight:bold;text-align:right">{sale.invoice_number}</td>
                                            </tr>
                                            <tr>
                                                <td style="color:#666;font-size:13px;padding:3px 0">Fecha</td>
                                                <td style="color:#1a1a2e;font-size:13px;text-align:right">{fecha}</td>
                                            </tr>
                                            <tr>
                                                <td style="color:#666;font-size:13px;padding:3px 0">Cajero</td>
                                                <td style="color:#1a1a2e;font-size:13px;text-align:right">{sale.cashier.full_name}</td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Tabla artículos -->
                    <tr>
                        <td style="padding:0 30px">
                            <p style="font-weight:bold;color:#1a1a2e;font-size:13px;margin:0 0 8px">ARTÍCULOS</p>
                            <table width="100%" cellpadding="0" cellspacing="0" style="border:1px solid #f0f0f0;border-radius:6px;overflow:hidden">
                                <tr style="background:#1a1a2e">
                                    <th style="padding:10px 12px;color:#fff;font-size:12px;text-align:left">Producto</th>
                                    <th style="padding:10px 12px;color:#fff;font-size:12px;text-align:center">Cant.</th>
                                    <th style="padding:10px 12px;color:#fff;font-size:12px;text-align:right">P. Unit.</th>
                                    <th style="padding:10px 12px;color:#fff;font-size:12px;text-align:right">Subtotal</th>
                                </tr>
                                {items_html}
                            </table>
                        </td>
                    </tr>

                    <!-- Total -->
                    <tr>
                        <td style="padding:16px 30px">
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td style="font-size:16px;font-weight:bold;color:#1a1a2e">TOTAL</td>
                                    <td style="font-size:20px;font-weight:bold;color:#1a1a2e;text-align:right">$ {sale.total:,}</td>
                                </tr>
                            </table>
                        </td>
                    </tr>

                    <!-- Footer -->
                    <tr>
                        <td style="background:#f8f8f8;padding:20px 30px;text-align:center;border-top:1px solid #f0f0f0">
                            <p style="margin:0;color:#999;font-size:12px">Este correo fue generado automáticamente por PyCommerceX.</p>
                            <p style="margin:4px 0 0;color:#999;font-size:12px">Por favor no respondas este mensaje.</p>
                        </td>
                    </tr>

                </table>
            </td></tr>
        </table>
    </body>
    </html>
    """

    texto = f"""
Hola {sale.customer_name},

Tu compra ha sido registrada exitosamente.

Factura: {sale.invoice_number}
Fecha: {fecha}
Cajero: {sale.cashier.full_name}

Productos:
{items_texto}

Total: $ {sale.total:,}

Gracias por tu compra.
PyCommerceX
    """.strip()

    pdf_bytes = _generar_pdf_factura(sale)

    _enviar_async(
        subject=f"Confirmación de compra - {sale.invoice_number}",
        html_content=html,
        text_content=texto,
        recipient_list=[sale.customer_email],
        pdf_bytes=pdf_bytes,
        pdf_filename=f"Factura_{sale.invoice_number}.pdf",
    )


def enviar_alerta_stock_bajo(product):
    destinatarios = _destinatarios_staff()
    if not destinatarios:
        return

    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="margin:0;padding:0;background:#f4f4f4;font-family:Arial,sans-serif">
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f4;padding:30px 0">
            <tr><td align="center">
                <table width="580" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08)">
                    <tr>
                        <td style="background:#f59e0b;padding:24px 30px;text-align:center">
                            <h1 style="margin:0;color:#fff;font-size:20px">⚠️ Alerta de Stock Bajo</h1>
                            <p style="margin:4px 0 0;color:#fff3cd;font-size:12px">PyCommerceX — Sistema de Gestión Comercial</p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding:28px 30px">
                            <p style="color:#333;font-size:14px;margin:0 0 20px">El siguiente producto ha alcanzado su stock mínimo:</p>
                            <table width="100%" cellpadding="0" cellspacing="0" style="background:#fffbeb;border-radius:6px;border-left:4px solid #f59e0b">
                                <tr>
                                    <td style="padding:16px 20px">
                                        <table width="100%">
                                            <tr>
                                                <td style="color:#666;font-size:13px;padding:3px 0">Producto</td>
                                                <td style="color:#1a1a2e;font-size:13px;font-weight:bold;text-align:right">{product.name}</td>
                                            </tr>
                                            <tr>
                                                <td style="color:#666;font-size:13px;padding:3px 0">Código</td>
                                                <td style="color:#1a1a2e;font-size:13px;text-align:right">{product.code}</td>
                                            </tr>
                                            <tr>
                                                <td style="color:#666;font-size:13px;padding:3px 0">Stock actual</td>
                                                <td style="color:#d97706;font-size:13px;font-weight:bold;text-align:right">{product.stock} unidades</td>
                                            </tr>
                                            <tr>
                                                <td style="color:#666;font-size:13px;padding:3px 0">Stock mínimo</td>
                                                <td style="color:#1a1a2e;font-size:13px;text-align:right">{product.min_stock} unidades</td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                            <p style="color:#666;font-size:13px;margin:20px 0 0">Se recomienda reabastecer este producto a la brevedad posible.</p>
                        </td>
                    </tr>
                    <tr>
                        <td style="background:#f8f8f8;padding:16px 30px;text-align:center;border-top:1px solid #f0f0f0">
                            <p style="margin:0;color:#999;font-size:12px">PyCommerceX — Notificación automática del sistema.</p>
                        </td>
                    </tr>
                </table>
            </td></tr>
        </table>
    </body>
    </html>
    """

    texto = f"""
Alerta de Stock Bajo — PyCommerceX

Producto: {product.name}
Código: {product.code}
Stock actual: {product.stock} unidades
Stock mínimo: {product.min_stock} unidades

Se recomienda reabastecer este producto pronto.
    """.strip()

    _enviar_async(
        subject=f"⚠️ Stock bajo - {product.name}",
        html_content=html,
        text_content=texto,
        recipient_list=destinatarios,
    )


def enviar_alerta_stock_agotado(product):
    destinatarios = _destinatarios_staff()
    if not destinatarios:
        return

    fecha = timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M')

    html = f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"></head>
    <body style="margin:0;padding:0;background:#f4f4f4;font-family:Arial,sans-serif">
        <table width="100%" cellpadding="0" cellspacing="0" style="background:#f4f4f4;padding:30px 0">
            <tr><td align="center">
                <table width="580" cellpadding="0" cellspacing="0" style="background:#ffffff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.08)">
                    <tr>
                        <td style="background:#dc2626;padding:24px 30px;text-align:center">
                            <h1 style="margin:0;color:#fff;font-size:20px">🚨 Producto Agotado</h1>
                            <p style="margin:4px 0 0;color:#fecaca;font-size:12px">PyCommerceX — Sistema de Gestión Comercial</p>
                        </td>
                    </tr>
                    <tr>
                        <td style="padding:28px 30px">
                            <p style="color:#333;font-size:14px;margin:0 0 20px">El siguiente producto se ha agotado completamente:</p>
                            <table width="100%" cellpadding="0" cellspacing="0" style="background:#fff5f5;border-radius:6px;border-left:4px solid #dc2626">
                                <tr>
                                    <td style="padding:16px 20px">
                                        <table width="100%">
                                            <tr>
                                                <td style="color:#666;font-size:13px;padding:3px 0">Producto</td>
                                                <td style="color:#1a1a2e;font-size:13px;font-weight:bold;text-align:right">{product.name}</td>
                                            </tr>
                                            <tr>
                                                <td style="color:#666;font-size:13px;padding:3px 0">Código</td>
                                                <td style="color:#1a1a2e;font-size:13px;text-align:right">{product.code}</td>
                                            </tr>
                                            <tr>
                                                <td style="color:#666;font-size:13px;padding:3px 0">Stock actual</td>
                                                <td style="color:#dc2626;font-size:13px;font-weight:bold;text-align:right">0 unidades</td>
                                            </tr>
                                            <tr>
                                                <td style="color:#666;font-size:13px;padding:3px 0">Fecha</td>
                                                <td style="color:#1a1a2e;font-size:13px;text-align:right">{fecha}</td>
                                            </tr>
                                        </table>
                                    </td>
                                </tr>
                            </table>
                            <p style="color:#666;font-size:13px;margin:20px 0 0">Se requiere reposición urgente para evitar pérdida de ventas.</p>
                        </td>
                    </tr>
                    <tr>
                        <td style="background:#f8f8f8;padding:16px 30px;text-align:center;border-top:1px solid #f0f0f0">
                            <p style="margin:0;color:#999;font-size:12px">PyCommerceX — Notificación automática del sistema.</p>
                        </td>
                    </tr>
                </table>
            </td></tr>
        </table>
    </body>
    </html>
    """

    texto = f"""
Producto Agotado — PyCommerceX

Producto: {product.name}
Código: {product.code}
Stock actual: 0 unidades
Fecha: {fecha}

Se requiere reposición urgente.
    """.strip()

    _enviar_async(
        subject=f"🚨 Producto agotado - {product.name}",
        html_content=html,
        text_content=texto,
        recipient_list=destinatarios,
    )
                 