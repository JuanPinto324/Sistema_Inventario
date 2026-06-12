from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Product, Return, Sale, SaleItem, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ("Datos del sistema", {"fields": ("full_name", "identification", "role")}),
    )
    list_display = ("identification", "full_name", "role", "is_active", "is_staff")
    search_fields = ("identification", "full_name", "username")


class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("invoice_number", "customer_name", "cashier", "total", "created_at", "is_returned")
    inlines = [SaleItemInline]


admin.site.register(Product)
admin.site.register(Return)
