# PyCommerceX

Sistema web para gestionar inventario y ventas, hecho con Django como proyecto final de Programacion Avanzada en la Universidad de La Guajira, 2026-I.

Repositorio: https://github.com/JuanPinto324/Sistema_Inventario
En produccion: https://pycommercex.onrender.com

---

## Por que lo hicimos

En muchos negocios pequeños el control de productos y ventas se lleva en cuadernos o en Excel. Eso hace complicado saber cuanto se vendio en el dia, cuales productos se estan agotando, quien hizo cada cosa y si los precios realmente dejan ganancia.

PyCommerceX resuelve eso: una sola aplicacion donde el jefe, los administradores y los cajeros pueden trabajar desde cualquier dispositivo, con todo registrado y organizado.

Teniamos una version anterior hecha en Flask, pero decidimos migrar todo a Django para el proyecto final porque nos daba mejor estructura y mas herramientas para escalar. Esta version es mas completa, esta desplegada en la nube y conectada a una base de datos real en Supabase.


---

## Que puede hacer

- Login con roles: jefe, administrador y cajero, cada uno con permisos distintos
- Si alguien falla la contrasena 5 veces seguidas, la cuenta se bloquea 10 minutos y aparece un contador en pantalla
- Cada usuario tiene una pagina de perfil donde puede cambiar su contrasena
- Punto de venta con carrito, busqueda de productos y facturas numeradas en orden
- Si se elimina un producto y queda un codigo libre, el sistema lo reutiliza automaticamente
- Inventario completo con CRUD de productos
- Historial de ventas con filtros por fecha
- Devoluciones que devuelven el stock automaticamente
- Registro de todo lo que hace cada usuario: cuando entro, que vendio, que modifico
- Reportes de ventas e inventario descargables en PDF y Excel
- Reporte de rentabilidad que muestra el margen de cada producto y si esta dejando perdida
- Correos automaticos con SendGrid:
  - Al cliente cuando compra, con la factura adjunta en PDF
  - Al jefe o admin cuando un producto baja del stock minimo
  - Al jefe o admin cuando un producto se agota

---

## Con que esta hecho

- Python 3.12 y Django 5.0
- PostgreSQL en produccion (Supabase), SQLite en local
- Render para el despliegue
- SendGrid para los correos
- ReportLab para los PDF
- OpenPyXL para los Excel
- WhiteNoise para los archivos estaticos
- Gunicorn como servidor

---

## Como correrlo local

```bash
git clone https://github.com/JuanPinto324/Sistema_Inventario.git
cd Sistema_Inventario
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Abrir en: http://127.0.0.1:8000

---

## Credenciales de prueba

| Campo | Valor |
|---|---|
| Identificacion | `0000000000` |
| Contrasena | `admin123` |
| Rol | Jefe |

---

## Variables de entorno

Localmente corre sin configuracion adicional usando SQLite. Para produccion se necesita un archivo `.env` basado en `.env.example`:

```
SECRET_KEY=clave-segura
DEBUG=False
DATABASE_URL=postgresql://...
SENDGRID_API_KEY=SG...
DEFAULT_FROM_EMAIL=correo_verificado_en_sendgrid
ADMIN_EMAIL=correo_del_admin
```


---

## Estructura

```
config/               Configuracion de Django
commerce/             Modelos, vistas, formularios, correos y reportes
commerce/management/  Comandos personalizados
commerce/migrations/  Migraciones
commerce/templatetags/ Filtros para templates
static/               CSS
templates/            HTML
requirements.txt      Dependencias
Procfile              Inicio en Render
runtime.txt           Version de Python
```

---

## Quienes lo hicimos

| Integrante            | Que hizo |
|---|---|
| Juan Andres Pinto     | Despliegue en Render con Supabase, correos automaticos con SendGrid: confirmacion de compra con PDF adjunto, alerta de stock bajo y alerta de producto agotado |
| Jose David Gonzales   | Bloqueo de login con contador regresivo, pagina de perfil con cambio de contrasena, registro de actividad por usuario |
| Jesus Enrique Mendoza | Reportes de ventas e inventario en PDF y Excel, reporte de rentabilidad con diagnostico de margenes, correccion de numeracion de facturas y productos |

---

## Uso de IA

Usamos Claude AI y Codex durante el desarrollo, principalmente para resolver errores de configuracion, ajustar el despliegue en Render y mejorar partes especificas como los reportes y los correos.