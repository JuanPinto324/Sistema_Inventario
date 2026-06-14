from django.core.management.base import BaseCommand
from commerce.models import User

class Command(BaseCommand):
    help = 'Crea el usuario jefe inicial'

    def handle(self, *args, **kwargs):
        if User.objects.filter(identificacion='1234567890').exists():
            self.stdout.write('El usuario ya existe, omitiendo.')
            return
        u = User()
        u.nombre = 'Juan Andres Pinto'
        u.identificacion = '1234567890'
        u.rol = 'jefe'
        u.set_password('admin123')
        u.save()
        self.stdout.write('Usuario jefe creado exitosamente.')
        