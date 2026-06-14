import threading
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import User


def _destinatarios_staff():
    return list(
        User.objects.filter(
            is_active=True,
            role__in=[User.ROLE_JEFE, User.ROLE_ADMIN],
        ).exclude(email="").values_list("email", flat=True)
    )


def _enviar_async(subject, message, recipient_list):
    """Envía el correo en un hilo separado para no bloquear la petición."""
    def _send():
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipient_list,
                fail_silently=True,
            )
        except Exception:
            pass
    threading.Thread(target=_send, daemon=True).start()


def enviar_confirmacion_compra(sale):
    if not sale.customer_email:
        return

    items_detalle = "\n".join(
        f"  - {item.product.name} x{item.quantity} = ${item.subtotal:,}"
        for item in sale.items.all()
    )

    mensaje = f"""
Hola {sale.customer_name},

Tu compra ha sido registrada exitosamente.

Factura: {sale.invoice_number}
Fecha: {timezone.localtime(sale.created_at).strftime('%d/%m/%Y %H:%M')}

Productos:
{items_detalle}

Total: ${sale.total:,}

Gracias por tu compra.
    """.strip()

    _enviar_async(
        subject=f"Confirmación de compra - {sale.invoice_number}",
        message=mensaje,
        recipient_list=[sale.customer_email],
    )


def enviar_alerta_stock_bajo(product):
    destinatarios = _destinatarios_staff()
    if not destinatarios:
        return

    mensaje = f"""
Alerta de Stock Bajo

Producto: {product.name}
Código: {product.code}
Stock actual: {product.stock} unidades
Stock mínimo: {product.min_stock} unidades

Se recomienda reabastecer este producto pronto.
    """.strip()

    _enviar_async(
        subject=f"⚠️ Stock bajo - {product.name}",
        message=mensaje,
        recipient_list=destinatarios,
    )


def enviar_alerta_stock_agotado(product):
    destinatarios = _destinatarios_staff()
    if not destinatarios:
        return

    mensaje = f"""
Alerta de Producto Agotado

Producto: {product.name}
Código: {product.code}
Stock actual: 0 unidades

Este producto está completamente agotado.
Se requiere reposición urgente.

Fecha: {timezone.localtime(timezone.now()).strftime('%d/%m/%Y %H:%M')}
    """.strip()

    _enviar_async(
        subject=f"🚨 Producto agotado - {product.name}",
        message=mensaje,
        recipient_list=destinatarios,
    )
    