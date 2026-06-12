# PyCommerceX

Sistema local de inventario y punto de venta construido con Django para el proyecto final de Programacion Avanzada.

## Problema que resuelve

Pequenos negocios necesitan controlar productos, stock, ventas, cajeros y devoluciones sin depender de hojas de calculo ni servicios externos. PyCommerceX permite operar una caja local, registrar facturas y mantener alertas de inventario bajo.

## Funcionalidades

- Autenticacion de usuarios con roles: jefe, administrador y cajero.
- Panel principal con ventas del dia, articulos vendidos y alertas de stock.
- CRUD de productos con codigo, costo, precio de venta, stock y stock minimo.
- Punto de venta con carrito, busqueda de productos y comprobante imprimible.
- Historial de ventas con filtros por fecha.
- Registro de devoluciones que restaura el stock vendido.
- Gestion de usuarios con correo, telefono y permisos por rol.

## Instalacion local

```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

Abre `http://127.0.0.1:8000`.

## Credenciales de demo

| Campo | Valor |
| --- | --- |
| Identificacion | `0000000000` |
| Contrasena | `admin123` |
| Rol | Jefe |

El administrador principal creado por defecto es `Juan Andres Pinto` y su correo es `juanpinto0206x@gmail.com`.

## Estructura

```text
config/      Configuracion principal de Django
commerce/    Modelos, vistas, formularios, rutas y comando seed_demo
static/      Estilos CSS del sistema
templates/   Pantallas HTML del sistema
```

## Uso de IA

Se uso Codex/ChatGPT como apoyo para convertir un prototipo previo en Flask a una aplicacion Django local, revisar los requisitos del documento del curso, estructurar modelos/vistas/templates y preparar instrucciones de ejecucion. El equipo debe estudiar el codigo y poder explicar cada flujo durante la sustentacion.

## Integrantes

- Nombre del integrante 1
- Nombre del integrante 2
