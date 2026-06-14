from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from .models import User


def _destinatarios_staff():
    """Retorna los correos de todos los jefes y admins activos."""
    return list(
        User.objects.filter(
            is_active=True,
            role__in=[User.ROLE_JEFE, User.ROLE_ADMIN],
        ).exclude(email="").values_list("email", flat=True)
    )


def enviar_confirmacion_compra(sale):
    """Correo al cliente cuando realiza una compra."""
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
Fecha: {sale.created_at.strftime('%d/%m/%Y %H:%M')}

Productos:
{items_detalle}

Total: ${sale.total:,}

Gracias por tu compra.
    """.strip()

    send_mail(
        subject=f"Confirmación de compra - {sale.invoice_number}",
        message=mensaje,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[sale.customer_email],
        fail_silently=True,
    )


def enviar_alerta_stock_bajo(product):
    """Correo a jefes y admins cuando un producto llega al stock mínimo."""
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

    send_mail(
        subject=f"⚠️ Stock bajo - {product.name}",
        message=mensaje,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=destinatarios,
        fail_silently=True,
    )


def enviar_alerta_stock_agotado(product):
    """Correo a jefes y admins cuando un producto llega a cero."""
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

    send_mail(
        subject=f"🚨 Producto agotado - {product.name}",
        message=mensaje,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=destinatarios,
        fail_silently=True,
    )
    