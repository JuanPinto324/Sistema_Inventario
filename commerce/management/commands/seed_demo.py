import os

from django.core.management.base import BaseCommand, CommandError

from commerce.models import Product, User


class Command(BaseCommand):
    help = "Crea el usuario jefe inicial. Los productos de demostración son opcionales."

    def add_arguments(self, parser):
        parser.add_argument(
            "--with-demo-products",
            action="store_true",
            help="Crea productos ficticios para desarrollo local.",
        )

    def handle(self, *args, **options):
        identification = os.environ.get("SEED_ADMIN_IDENTIFICATION")
        password = os.environ.get("SEED_ADMIN_PASSWORD")
        full_name = os.environ.get("SEED_ADMIN_FULL_NAME")
        email = os.environ.get("SEED_ADMIN_EMAIL")

        if not all([identification, password, full_name, email]):
            raise CommandError(
                "Faltan variables: SEED_ADMIN_IDENTIFICATION, "
                "SEED_ADMIN_PASSWORD, SEED_ADMIN_FULL_NAME y SEED_ADMIN_EMAIL."
            )

        user, created = User.objects.get_or_create(
            identification=identification,
            defaults={
                "username": identification,
                "full_name": full_name,
                "email": email,
                "role": User.ROLE_JEFE,
                "is_staff": True,
                "is_superuser": True,
            },
        )

        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(
                self.style.SUCCESS(f"Usuario jefe creado: {identification}")
            )
        else:
            self.stdout.write("El usuario jefe ya existe.")

        if options["with_demo_products"]:
            products = [
                ("PROD-001", "Producto de ejemplo 1", 1000, 1500, 10, 2),
                ("PROD-002", "Producto de ejemplo 2", 2000, 3000, 5, 1),
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
            self.stdout.write(self.style.SUCCESS("Productos de demostración creados."))