from django.core.management.base import BaseCommand

from commerce.models import Product, User


class Command(BaseCommand):
    help = "Crea el usuario inicial y algunos productos de ejemplo."

    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(
            identification="0000000000",
            defaults={
                "username": "0000000000",
                "full_name": "Juan Andres Pinto",
                "email": "juanpinto0206x@gmail.com",
                "role": User.ROLE_JEFE,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        if created:
            user.set_password("admin123")
            user.save()
            self.stdout.write(self.style.SUCCESS("Usuario jefe creado: 0000000000 / admin123"))
        else:
            user.full_name = "Juan Andres Pinto"
            user.email = "juanpinto0206x@gmail.com"
            user.is_staff = True
            user.is_superuser = True
            user.save(update_fields=["full_name", "email", "is_staff", "is_superuser"])
            self.stdout.write("El usuario jefe ya existe.")

        products = [
            ("PROD-001", "Arroz Diana 500g", 2200, 3200, 24, 5),
            ("PROD-002", "Aceite vegetal 1L", 7800, 9800, 12, 4),
            ("PROD-003", "Cafe molido 250g", 6500, 8500, 8, 3),
            ("PROD-004", "Azucar blanca 1kg", 3600, 4800, 2, 5),
        ]
        for code, name, cost, sell, stock, min_stock in products:
            Product.objects.get_or_create(
                code=code,
                defaults={
                    "name": name,
                    "cost_price": cost,
                    "sell_price": sell,
                    "stock": stock,
                    "min_stock": min_stock,
                },
            )
        self.stdout.write(self.style.SUCCESS("Datos de demostracion listos."))
