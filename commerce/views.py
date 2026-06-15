import json
import time
from datetime import datetime, timedelta
from functools import wraps

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F, Q, Sum
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import LoginForm, ProductForm, UserForm
from .models import Product, Return, Sale, SaleItem, User, ActivityLog
from .emails import enviar_confirmacion_compra, enviar_alerta_stock_bajo, enviar_alerta_stock_agotado
from .activity import registrar

from .reportes import (
    export_ventas_pdf,
    export_ventas_excel,
    export_inventario_pdf,
    export_inventario_excel,
    export_rentabilidad_excel,
    export_rentabilidad_pdf,
)


def staff_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(f"{reverse('login')}?next={request.path}")
        if request.user.role not in (User.ROLE_JEFE, User.ROLE_ADMIN):
            return render(request, "403.html", status=403)
        return view_func(request, *args, **kwargs)
    return wrapper


def home(request):
    if not request.user.is_authenticated:
        return redirect("login")
    return redirect("dashboard" if request.user.is_staff_member else "pos_index")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("home")

    form = LoginForm(request.POST or None)
    blocked_seconds = 0

    if request.method == "POST" and form.is_valid():
        identification = form.cleaned_data["identification"].strip()
        password = form.cleaned_data["password"]

        cache_key = f"login_attempts_{identification}"
        block_key = f"login_block_time_{identification}"
        attempts = request.session.get(cache_key, 0)
        block_time = request.session.get(block_key, None)

        if block_time:
            segundos_restantes = int(block_time - time.time())
            if segundos_restantes > 0:
                blocked_seconds = segundos_restantes
                return render(request, "auth/login.html", {"form": form, "blocked_seconds": blocked_seconds})
            else:
                request.session[cache_key] = 0
                request.session[block_key] = None

        user = authenticate(request, username=identification, password=password)
        if user and user.is_active:
            request.session[cache_key] = 0
            request.session[block_key] = None
            login(request, user)
            registrar(user, "login", request=request)
            messages.success(request, f"Bienvenido, {user.full_name}.")
            return redirect(request.GET.get("next") or "home")

        attempts += 1
        request.session[cache_key] = attempts
        restantes = 5 - attempts

        if attempts >= 5:
            request.session[block_key] = time.time() + 600
            request.session.set_expiry(600)
            blocked_seconds = 600
            return render(request, "auth/login.html", {"form": form, "blocked_seconds": blocked_seconds})
        else:
            messages.error(request, f"Identificacion o contrasena incorrecta. Te quedan {restantes} intentos.")

    return render(request, "auth/login.html", {"form": form, "blocked_seconds": blocked_seconds})


def logout_view(request):
    registrar(request.user, "logout", request=request)
    logout(request)
    messages.info(request, "Sesion cerrada correctamente.")
    return redirect("login")


@staff_required
def dashboard(request):
    today = timezone.localdate()
    start = timezone.make_aware(datetime.combine(today, datetime.min.time()))
    end = timezone.make_aware(datetime.combine(today, datetime.max.time()))

    sales_today = Sale.objects.filter(created_at__range=(start, end), is_returned=False)
    total_today = sum(sale.total for sale in sales_today)
    invoices_today = sales_today.count()
    items_today = SaleItem.objects.filter(sale__in=sales_today).aggregate(total=Sum("quantity"))["total"] or 0

    low_stock = Product.objects.filter(is_active=True, stock__gt=0, stock__lte=F("min_stock"))
    out_stock = Product.objects.filter(is_active=True, stock=0)

    return render(
        request,
        "dashboard/index.html",
        {
            "total_today": total_today,
            "invoices_today": invoices_today,
            "items_today": items_today,
            "total_products": Product.objects.filter(is_active=True).count(),
            "low_stock_count": low_stock.count(),
            "out_of_stock_count": out_stock.count(),
            "alert_products": list(low_stock) + list(out_stock),
        },
    )


def _next_product_code():
    used = set()
    for code in Product.objects.filter(is_active=True, code__startswith="PROD-").values_list("code", flat=True):
        try:
            used.add(int(code.split("-")[1]))
        except (IndexError, ValueError):
            continue
    number = 1
    while number in used:
        number += 1
    return f"PROD-{number:03d}"


@staff_required
def inventory_index(request):
    q = request.GET.get("q", "").strip()
    products = Product.objects.filter(is_active=True)
    if q:
        products = products.filter(Q(name__icontains=q) | Q(code__icontains=q))
    return render(request, "inventory/index.html", {"products": products, "q": q})


@staff_required
def inventory_new(request):
    initial = {"code": _next_product_code(), "stock": 0, "min_stock": 5}
    form = ProductForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        code = form.cleaned_data["code"].upper().strip()
        inactive = Product.objects.filter(code=code, is_active=False).first()
        if inactive:
            for field, value in form.cleaned_data.items():
                setattr(inactive, field, value)
            inactive.code = code
            inactive.is_active = True
            inactive.save()
            messages.success(request, f'Producto "{inactive.name}" restaurado exitosamente.')
            return redirect("inventory_index")
        if Product.objects.filter(code=code, is_active=True).exists():
            messages.error(request, "Ya existe un producto con ese codigo.")
        else:
            product = form.save(commit=False)
            product.code = code
            product.save()
            registrar(request.user, "producto_creado", f"{product.name} ({product.code})", request)
            messages.success(request, f'Producto "{product.name}" registrado exitosamente.')
            return redirect("inventory_index")
    return render(request, "inventory/form.html", {"form": form, "product": None, "action": "Nuevo"})


@staff_required
def inventory_edit(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    form = ProductForm(request.POST or None, instance=product)
    form.fields["code"].disabled = True
    if request.method == "POST" and form.is_valid():
        form.save()
        registrar(request.user, "producto_editado", f"{product.name} ({product.code})", request)
        messages.success(request, "Producto actualizado.")
        return redirect("inventory_index")
    return render(request, "inventory/form.html", {"form": form, "product": product, "action": "Editar"})


@require_POST
@staff_required
def inventory_delete(request, product_id):
    product = get_object_or_404(Product, pk=product_id)
    product.is_active = False
    product.save(update_fields=["is_active"])
    registrar(request.user, "producto_eliminado", f"{product.name} ({product.code})", request)
    messages.warning(request, f'Producto "{product.name}" eliminado.')
    return redirect("inventory_index")


@login_required
def product_search(request):
    q = request.GET.get("q", "").strip()
    products = Product.objects.filter(is_active=True, stock__gt=0)
    if q:
        products = products.filter(Q(name__icontains=q) | Q(code__icontains=q))
    data = [
        {"id": p.id, "code": p.code, "name": p.name, "sell_price": p.sell_price, "stock": p.stock}
        for p in products[:10]
    ]
    return JsonResponse(data, safe=False)


@login_required
def pos_index(request):
    products = Product.objects.filter(is_active=True, stock__gt=0).order_by("name")
    top_ids = (
        SaleItem.objects.values("product_id")
        .annotate(total_sold=Sum("quantity"))
        .order_by("-total_sold")[:5]
    )
    top_products = Product.objects.filter(
        id__in=[row["product_id"] for row in top_ids], is_active=True, stock__gt=0
    )
    return render(request, "pos/index.html", {"products": products, "top_products": top_products})


def _next_invoice():
    used = set()
    for invoice in Sale.objects.filter(invoice_number__startswith="FAC-").values_list("invoice_number", flat=True):
        try:
            used.add(int(invoice.split("-")[1]))
        except (IndexError, ValueError):
            continue
    number = 1
    while number in used:
        number += 1
    return f"FAC-{number:06d}"


@require_POST
@login_required
@transaction.atomic
def pos_complete(request):
    data = json.loads(request.body.decode("utf-8"))
    customer_id = data.get("customer_id", "").strip()
    customer_name = data.get("customer_name", "").strip()
    items = data.get("items", [])

    if not customer_id or not customer_name:
        return JsonResponse({"ok": False, "msg": "Datos del cliente incompletos."}, status=400)
    if not items:
        return JsonResponse({"ok": False, "msg": "El carrito esta vacio."}, status=400)

    validated = []
    total = 0
    for item in items:
        product = Product.objects.select_for_update().get(pk=item["product_id"])
        quantity = int(item["quantity"])
        if product.stock < quantity:
            return JsonResponse({"ok": False, "msg": f"Stock insuficiente para {product.name}."}, status=400)
        subtotal = product.sell_price * quantity
        total += subtotal
        validated.append((product, quantity, product.sell_price, subtotal))

    sale = Sale.objects.create(
        invoice_number=_next_invoice(),
        customer_id=customer_id,
        customer_name=customer_name,
        customer_phone=data.get("customer_phone", "").strip(),
        customer_email=data.get("customer_email", "").strip(),
        total=total,
        cashier=request.user,
    )
    for product, quantity, unit_price, subtotal in validated:
        SaleItem.objects.create(
            sale=sale,
            product=product,
            quantity=quantity,
            unit_price=unit_price,
            subtotal=subtotal,
        )
        product.stock -= quantity
        product.save(update_fields=["stock"])

    registrar(request.user, "venta", f"Factura {sale.invoice_number} - ${sale.total:,}", request)

    enviar_confirmacion_compra(sale)
    for product, quantity, unit_price, subtotal in validated:
        p = Product.objects.get(pk=product.id)
        if p.stock == 0:
            enviar_alerta_stock_agotado(p)
        elif p.stock <= p.min_stock:
            enviar_alerta_stock_bajo(p)

    return JsonResponse({"ok": True, "sale_id": sale.id, "invoice": sale.invoice_number})


@login_required
def pos_ticket(request, sale_id):
    sale = get_object_or_404(Sale, pk=sale_id)
    return render(request, "pos/ticket.html", {"sale": sale})


@staff_required
def sales_index(request):
    filter_type = request.GET.get("filter", "today")
    date_from = request.GET.get("from", "")
    date_to = request.GET.get("to", "")
    today = timezone.localdate()
    sales = Sale.objects.all()

    if filter_type == "today":
        start_date = end_date = today
    elif filter_type == "yesterday":
        start_date = end_date = today - timedelta(days=1)
    elif filter_type == "range" and date_from and date_to:
        start_date = datetime.strptime(date_from, "%Y-%m-%d").date()
        end_date = datetime.strptime(date_to, "%Y-%m-%d").date()
    else:
        start_date = end_date = None

    if start_date and end_date:
        start = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
        end = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))
        sales = sales.filter(created_at__range=(start, end))
        export_from = start_date.isoformat()
        export_to = end_date.isoformat()
    else:
        export_from = ""
        export_to = ""

    sales = list(sales.select_related("cashier").prefetch_related("items"))
    active_sales = [sale for sale in sales if not sale.is_returned]
    return render(
        request,
        "sales/index.html",
        {
            "sales": sales,
            "total_amount": sum(sale.total for sale in active_sales),
            "total_invoices": len(active_sales),
            "total_items": sum(sum(item.quantity for item in sale.items.all()) for sale in active_sales),
            "total_returns": len([sale for sale in sales if sale.is_returned]),
            "filter_type": filter_type,
            "date_from": date_from,
            "date_to": date_to,
            "export_from": export_from,
            "export_to": export_to,
        },
    )


@staff_required
def sales_detail(request, sale_id):
    sale = get_object_or_404(Sale.objects.select_related("cashier").prefetch_related("items__product"), pk=sale_id)
    return render(request, "sales/detail.html", {"sale": sale})


@require_POST
@staff_required
@transaction.atomic
def sale_return(request, sale_id):
    sale = get_object_or_404(Sale.objects.select_for_update().prefetch_related("items__product"), pk=sale_id)
    if sale.is_returned:
        messages.warning(request, "Esta venta ya fue devuelta.")
        return redirect("sales_detail", sale_id=sale.id)

    for item in sale.items.all():
        item.product.stock += item.quantity
        item.product.save(update_fields=["stock"])
    sale.is_returned = True
    sale.save(update_fields=["is_returned"])
    Return.objects.create(
        sale=sale,
        reason=request.POST.get("reason", "").strip(),
        processed_by=request.user,
    )
    registrar(request.user, "devolucion", f"Factura {sale.invoice_number}", request)
    messages.success(request, f"Devolucion de la factura {sale.invoice_number} procesada.")
    return redirect("sales_detail", sale_id=sale.id)


def _allowed_roles_for(role):
    if role == User.ROLE_JEFE:
        return [User.ROLE_JEFE, User.ROLE_ADMIN, User.ROLE_CAJERO]
    return [User.ROLE_CAJERO]


@staff_required
def users_index(request):
    users = User.objects.filter(is_active=True).order_by("full_name")
    return render(request, "users/index.html", {"users": users})


@staff_required
def users_new(request):
    allowed = _allowed_roles_for(request.user.role)
    form = UserForm(request.POST or None, allowed_roles=allowed)
    if request.method == "POST" and form.is_valid():
        if form.cleaned_data["role"] not in allowed:
            messages.error(request, "No tienes permiso para crear usuarios con ese rol.")
        else:
            user = form.save()
            registrar(request.user, "usuario_creado", user.full_name, request)
            messages.success(request, f'Usuario "{user.full_name}" creado exitosamente.')
            return redirect("users_index")
    return render(request, "users/form.html", {"form": form, "user_obj": None, "action": "Nuevo", "allowed_roles": allowed})


@staff_required
def users_edit(request, user_id):
    user_obj = get_object_or_404(User, pk=user_id)
    if request.user.role == User.ROLE_ADMIN and user_obj.role != User.ROLE_CAJERO:
        messages.error(request, "No tienes permiso para editar este usuario.")
        return redirect("users_index")
    allowed = _allowed_roles_for(request.user.role)
    form = UserForm(request.POST or None, instance=user_obj, allowed_roles=allowed)
    if request.method == "POST" and form.is_valid():
        form.save()
        registrar(request.user, "usuario_editado", user_obj.full_name, request)
        messages.success(request, "Usuario actualizado.")
        return redirect("users_index")
    return render(request, "users/form.html", {"form": form, "user_obj": user_obj, "action": "Editar", "allowed_roles": allowed})


@require_POST
@staff_required
def users_delete(request, user_id):
    user_obj = get_object_or_404(User, pk=user_id)
    if user_obj.id == request.user.id:
        messages.error(request, "No puedes eliminar tu propia cuenta.")
    elif request.user.role == User.ROLE_ADMIN and user_obj.role != User.ROLE_CAJERO:
        messages.error(request, "No tienes permiso para eliminar este usuario.")
    else:
        user_obj.is_active = False
        user_obj.save(update_fields=["is_active"])
        registrar(request.user, "usuario_eliminado", user_obj.full_name, request)
        messages.warning(request, f'Usuario "{user_obj.full_name}" eliminado.')
    return redirect("users_index")


@login_required
def cambiar_password(request):
    if request.method == "POST":
        password_actual = request.POST.get("password_actual", "").strip()
        password_nuevo = request.POST.get("password_nuevo", "").strip()
        password_confirmar = request.POST.get("password_confirmar", "").strip()

        if not request.user.check_password(password_actual):
            messages.error(request, "La contrasena actual es incorrecta.")
        elif len(password_nuevo) < 6:
            messages.error(request, "La nueva contrasena debe tener al menos 6 caracteres.")
        elif password_nuevo != password_confirmar:
            messages.error(request, "Las contrasenas nuevas no coinciden.")
        else:
            request.user.set_password(password_nuevo)
            request.user.save()
            update_session_auth_hash(request, request.user)
            messages.success(request, "Contrasena actualizada correctamente.")
            return redirect("perfil")

    return render(request, "auth/perfil.html")


@staff_required
def activity_log(request):
    user_filter = request.GET.get("user", "")
    action_filter = request.GET.get("action", "")

    logs = ActivityLog.objects.select_related("user").all()

    if user_filter:
        logs = logs.filter(user__id=user_filter)
    if action_filter:
        logs = logs.filter(action=action_filter)

    logs = logs[:200]
    users = User.objects.filter(is_active=True).order_by("full_name")

    return render(request, "users/activity.html", {
        "logs": logs,
        "users": users,
        "user_filter": user_filter,
        "action_filter": action_filter,
        "action_choices": ActivityLog.ACTION_CHOICES,
    })

@staff_required
def reporte_ventas_pdf(request):
    date_from = request.GET.get("from", "")
    date_to = request.GET.get("to", "")
    sales = Sale.objects.all().select_related("cashier").prefetch_related("items")
    if date_from and date_to:
        from datetime import datetime
        start = timezone.make_aware(datetime.strptime(date_from, "%Y-%m-%d").replace(hour=0, minute=0))
        end = timezone.make_aware(datetime.strptime(date_to, "%Y-%m-%d").replace(hour=23, minute=59))
        sales = sales.filter(created_at__range=(start, end))
    return export_ventas_pdf(list(sales), date_from, date_to)


@staff_required
def reporte_ventas_excel(request):
    date_from = request.GET.get("from", "")
    date_to = request.GET.get("to", "")
    sales = Sale.objects.all().select_related("cashier").prefetch_related("items")
    if date_from and date_to:
        from datetime import datetime
        start = timezone.make_aware(datetime.strptime(date_from, "%Y-%m-%d").replace(hour=0, minute=0))
        end = timezone.make_aware(datetime.strptime(date_to, "%Y-%m-%d").replace(hour=23, minute=59))
        sales = sales.filter(created_at__range=(start, end))
    return export_ventas_excel(list(sales), date_from, date_to)


@staff_required
def reporte_inventario_pdf(request):
    products = Product.objects.filter(is_active=True).order_by("name")
    return export_inventario_pdf(list(products))


@staff_required
def reporte_inventario_excel(request):
    products = Product.objects.filter(is_active=True).order_by("name")
    return export_inventario_excel(list(products))


@staff_required
def reporte_rentabilidad_excel(request):
    products = Product.objects.filter(is_active=True).order_by("name")
    return export_rentabilidad_excel(list(products))


@staff_required
def reporte_rentabilidad_pdf(request):
    products = Product.objects.filter(is_active=True).order_by("name")
    return export_rentabilidad_pdf(list(products))


@staff_required
def reportes_index(request):
    products = Product.objects.filter(is_active=True).order_by("name")
    profitability_rows = []
    total_cost = 0
    total_sale_value = 0
    total_profit = 0
    low_margin_count = 0
    loss_count = 0

    for product in products:
        unit_profit = product.sell_price - product.cost_price
        margin = (unit_profit / product.sell_price * 100) if product.sell_price else 0
        stock_cost = product.cost_price * product.stock
        stock_sale_value = product.sell_price * product.stock
        stock_profit = unit_profit * product.stock

        total_cost += stock_cost
        total_sale_value += stock_sale_value
        total_profit += stock_profit
        if unit_profit < 0:
            loss_count += 1
        elif margin < 20:
            low_margin_count += 1

        profitability_rows.append({
            "product": product,
            "unit_profit": unit_profit,
            "margin": margin,
            "stock_profit": stock_profit,
        })

    profitability_rows.sort(key=lambda row: row["margin"])
    overall_margin = (total_profit / total_sale_value * 100) if total_sale_value else 0

    return render(request, "reportes/index.html", {
        "profitability_rows": profitability_rows,
        "profitability_summary": {
            "total_products": products.count(),
            "total_cost": total_cost,
            "total_sale_value": total_sale_value,
            "total_profit": total_profit,
            "overall_margin": overall_margin,
            "low_margin_count": low_margin_count,
            "loss_count": loss_count,
        },
    })
    
