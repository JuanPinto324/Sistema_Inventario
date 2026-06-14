from django.core.management.base import BaseCommand
from commerce.models import User

class Command(BaseCommand):
    help = 'Crea el usuario jefe inicial'

    def handle(self, *args, **kwargs):
        if User.objects.filter(identification='1234567890').exists():
            self.stdout.write('El usuario ya existe, omitiendo.')
            return
        u = User()
        u.full_name = 'Juan Andres Pinto'
        u.identification = '1234567890'
        u.username = '1234567890'
        u.role = 'jefe'
        u.is_staff = True
        u.set_password('admin123')
        u.save()
        self.stdout.write('Usuario jefe creado exitosamente.')
        