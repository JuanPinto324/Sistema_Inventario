from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone


class User(AbstractUser):
    ROLE_JEFE = "jefe"
    ROLE_ADMIN = "administrador"
    ROLE_CAJERO = "cajero"
    ROLE_CHOICES = [
        (ROLE_JEFE, "Jefe"),
        (ROLE_ADMIN, "Administrador"),
        (ROLE_CAJERO, "Cajero"),
    ]

    full_name = models.CharField(max_length=120)
    identification = models.CharField(max_length=30, unique=True)
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default=ROLE_CAJERO)
    created_at = models.DateTimeField(default=timezone.now)

    USERNAME_FIELD = "identification"
    REQUIRED_FIELDS = ["username", "full_name"]

    @property
    def role_color(self):
        return {
            self.ROLE_JEFE: "#FFD700",
            self.ROLE_ADMIN: "#E53E3E",
            self.ROLE_CAJERO: "#718096",
        }.get(self.role, "#718096")

    @property
    def role_label(self):
        return dict(self.ROLE_CHOICES).get(self.role, self.role.title())

    @property
    def is_staff_member(self):
        return self.role in (self.ROLE_JEFE, self.ROLE_ADMIN)

    def __str__(self):
        return f"{self.full_name} [{self.role_label}]"


class Product(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=120)
    cost_price = models.PositiveIntegerField(default=0)
    sell_price = models.PositiveIntegerField(default=0)
    stock = models.PositiveIntegerField(default=0)
    min_stock = models.PositiveIntegerField(default=5)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    @property
    def status(self):
        if self.stock == 0:
            return "Agotado"
        if self.stock <= self.min_stock:
            return "Bajo Stock"
        return "Disponible"

    @property
    def status_class(self):
        if self.stock == 0:
            return "status-out"
        if self.stock <= self.min_stock:
            return "status-low"
        return "status-ok"

    def __str__(self):
        return f"{self.code} - {self.name}"


class Sale(models.Model):
    invoice_number = models.CharField(max_length=20, unique=True)
    customer_id = models.CharField(max_length=30)
    customer_name = models.CharField(max_length=120)
    customer_phone = models.CharField(max_length=20, blank=True)
    customer_email = models.EmailField(max_length=120, blank=True)
    total = models.PositiveIntegerField(default=0)
    cashier = models.ForeignKey(User, on_delete=models.PROTECT, related_name="sales")
    created_at = models.DateTimeField(default=timezone.now)
    is_returned = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.invoice_number} - ${self.total}"


class SaleItem(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="sale_items")
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.PositiveIntegerField()
    subtotal = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.product.name} x {self.quantity}"


class Return(models.Model):
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="returns")
    reason = models.TextField(blank=True)
    processed_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="returns_processed")
    created_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"Devolucion {self.sale.invoice_number}"
