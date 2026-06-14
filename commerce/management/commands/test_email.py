from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings


class Command(BaseCommand):
    help = 'Prueba el envío de correo'

    def handle(self, *args, **kwargs):
        self.stdout.write(f"EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
        self.stdout.write(f"DEFAULT_FROM_EMAIL: {settings.DEFAULT_FROM_EMAIL}")
        self.stdout.write(f"ADMIN_EMAIL: {settings.ADMIN_EMAIL}")
        self.stdout.write("Enviando correo de prueba...")
        try:
            send_mail(
                subject="Prueba PyCommerceX",
                message="Si recibes este correo, el sistema de emails funciona.",
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.ADMIN_EMAIL],
                fail_silently=False,
            )
            self.stdout.write(self.style.SUCCESS("Correo enviado exitosamente."))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error: {e}"))
            
