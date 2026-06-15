# PyCommerceX - Sistema de Inventario y Ventas

Aplicacion web construida con Django para el proyecto final de Programacion Avanzada de la Universidad de La Guajira. El sistema permite administrar inventario, ventas, usuarios, devoluciones, reportes y notificaciones automaticas para un negocio pequeno o mediano.

Repositorio: https://github.com/JuanPinto324/Sistema_Inventario

## Problema que resuelve

Muchos negocios pequenos controlan sus productos, ventas y existencias con hojas de calculo o registros manuales. Esto dificulta saber cuanto se vendio, que productos estan por agotarse, quien realizo una operacion y que rentabilidad tiene el inventario.

PyCommerceX centraliza esos procesos en una aplicacion web con roles de usuario, punto de venta, control de stock, reportes exportables y alertas automaticas por correo.

## Funcionalidades principales

- Autenticacion con roles: jefe, administrador y cajero.
- Bloqueo temporal de login despues de 5 intentos fallidos, con contador regresivo.
- Perfil de usuario con visualizacion de datos y cambio de contrasena.
- Punto de venta con carrito, busqueda de productos y generacion de factura.
- Numeracion consecutiva de facturas y reutilizacion de codigos libres de productos activos.
- CRUD de productos con codigo, costo, precio de venta, stock y stock minimo.
- Historial de ventas con filtros por fecha.
- Devoluciones que restauran automaticamente el stock vendido.
- Registro de actividad por usuario: login, logout, ventas, devoluciones, productos y usuarios.
- Reportes de ventas e inventario exportables a PDF y Excel.
- Reporte de rentabilidad con costo, valor de venta, utilidad potencial, margen y diagnostico.
- Exportacion de rentabilidad a PDF y Excel.
- Correos automaticos con SendGrid:
  - Confirmacion de compra al cliente.
  - Alerta de stock bajo al jefe o administrador.
  - Alerta de producto agotado al jefe o administrador.

## Tecnologias utilizadas

- Python
- Django
- SQLite para desarrollo local
- PostgreSQL/Supabase para produccion
- Render para despliegue
- SendGrid para envio de correos
- ReportLab para generacion de PDF
- OpenPyXL para generacion de Excel
- WhiteNoise para archivos estaticos en produccion

## Instalacion local

1. Clonar el repositorio:

```bash
git clone https://github.com/JuanPinto324/Sistema_Inventario.git
cd Sistema_Inventario
```

2. Crear y activar entorno virtual:

```bash
python -m venv venv
venv\Scripts\activate
```

3. Instalar dependencias:

```bash
pip install -r requirements.txt
```

4. Ejecutar migraciones y datos de prueba:

```bash
python manage.py migrate
python manage.py seed_demo
```

5. Iniciar servidor local:

```bash
python manage.py runserver
```

Abrir en el navegador:

```text
http://127.0.0.1:8000
```

## Credenciales de demo

| Campo | Valor |
| --- | --- |
| Identificacion | `0000000000` |
| Contrasena | `admin123` |
| Rol | Jefe |

## Variables de entorno

El proyecto puede ejecutarse localmente con SQLite sin variables adicionales. Para produccion en Render/Supabase y envio de correos se usan variables de entorno.

Ejemplo:

```text
SECRET_KEY=clave-segura
DEBUG=False
DATABASE_URL=postgresql://...
SENDGRID_API_KEY=SG...
DEFAULT_FROM_EMAIL=correo_verificado_en_sendgrid
ADMIN_EMAIL=correo_admin
EMAIL_TIMEOUT=15
```

Notas:

- No se debe subir un archivo `.env` real al repositorio.
- `DEFAULT_FROM_EMAIL` debe ser un remitente verificado en SendGrid.
- Si no hay `SENDGRID_API_KEY`, Django usa el backend de consola para desarrollo local.

## Estructura del proyecto

```text
config/                     Configuracion principal de Django
commerce/                   Modelos, vistas, formularios, correos y reportes
commerce/management/        Comandos personalizados, incluido seed_demo
commerce/migrations/        Migraciones de base de datos
commerce/templatetags/      Filtros personalizados para templates
static/                     Archivos CSS
templates/                  Pantallas HTML del sistema
requirements.txt            Dependencias del proyecto
Procfile                    Comando de ejecucion en Render
runtime.txt                 Version de Python para Render
```

## Integrantes y aportes

| Integrante | Aporte principal |
| --- | --- |
| Juan Andres Pinto Meza | Notificaciones automaticas por correo con SendGrid: confirmacion de compra, stock bajo y producto agotado. |
| Jose David Gonzales | Seguridad y usuarios: limite de intentos de login, perfil con cambio de contrasena y registro de actividad. |
| Jesus Enrique Mendoza | Reportes: exportacion de ventas/inventario, reporte de rentabilidad, diagnostico de margenes y exportaciones PDF/Excel. |

## Uso de IA

Durante el desarrollo se usaron herramientas de IA como Codex/ChatGPT y Claude AI como apoyo para:

- Migrar la idea inicial de Flask a Django.
- Organizar modelos, vistas, templates y rutas.
- Revisar errores de configuracion y despliegue.
- Mejorar reportes, exportaciones y notificaciones.
- Documentar el proyecto y preparar la sustentacion.

El equipo debe poder explicar el codigo durante la sustentacion, especialmente las funcionalidades que implemento cada integrante.

## Sustentacion sugerida

Para una demo corta de 10 minutos se recomienda mostrar:

1. Inicio de sesion y roles.
2. Creacion o edicion de un producto.
3. Venta desde el punto de venta.
4. Factura generada y correo de confirmacion.
5. Historial de ventas y devolucion.
6. Reportes PDF/Excel y rentabilidad.
7. Registro de actividad por usuario.
