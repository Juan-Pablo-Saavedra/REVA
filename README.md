# SIGR — Sistema Integral de Gestión de Restaurante

Aplicación web (API REST) para gestionar la operación diaria de un restaurante:
autenticación por roles, menú digital, pedidos, reservas, cierre de caja y reportes de ventas.

Este repositorio contiene la **versión base (línea base `v1.0.0-baseline`)** desarrollada para la
actividad AA2 de *Gestión del Software* (Unidad 2, Gestión de la configuración).

- **Repositorio:** https://github.com/Juan-Pablo-Saavedra/REVA
- **Rama estable:** `main`
- **Línea base:** etiqueta `v1.0.0-baseline`
- **Licencia:** MIT (ver `LICENSE.txt`)

## Módulos incluidos en la línea base

| Módulo | Archivo | Qué hace |
|---|---|---|
| Autenticación | `sigr/auth.py` | Registro, inicio y cierre de sesión; roles `cliente`, `mesero`, `administrador` |
| Menú digital | `sigr/menu.py` | CRUD de categorías y platos; consulta pública del menú |
| Pedidos | `sigr/pedidos.py` | Registro de pedidos y seguimiento de su estado (con mesas en `sigr/mesas.py`) |
| Reservas | `sigr/reservas.py` | Reservas por fecha y hora, con control de solapamiento |
| Caja y reportes | `sigr/caja.py` | Cierre de caja y reporte de ventas diario |

## Requisitos

- Python 3.11 o superior (probado con 3.13)
- pip

## Instalación y ejecución

```bash
git clone https://github.com/Juan-Pablo-Saavedra/REVA.git
cd REVA
python3 -m venv .venv
source .venv/bin/activate          # en Windows: .venv\Scripts\activate
pip install -r requirements.txt

export SIGR_SECRET_KEY="una-clave-larga-y-aleatoria"   # en Windows: set SIGR_SECRET_KEY=...
flask --app sigr init-db                               # crea la base de datos
flask --app sigr crear-admin admin@restaurante.com "Nombre Admin"   # pide la clave
python run.py                                          # http://127.0.0.1:5000
```

Comprobación rápida: `curl http://127.0.0.1:5000/salud` devuelve `{"estado":"ok","version":"1.0.0"}`.

## Pruebas

```bash
python -m pytest -q
```

La suite tiene 78 pruebas (unitarias por módulo y una de integración que recorre un día completo
de operación).

## Resumen de la API

| Método y ruta | Rol requerido |
|---|---|
| `POST /auth/registro`, `POST /auth/login`, `POST /auth/logout`, `GET /auth/yo` | público / sesión |
| `GET /menu`, `GET /menu/platos/<id>` | público |
| `POST/PUT/DELETE /menu/categorias…`, `POST/PUT/DELETE /menu/platos…` | administrador |
| `GET /mesas` · `POST /mesas` | sesión · administrador |
| `POST /pedidos`, `GET /pedidos`, `GET /pedidos/<id>` | sesión (el cliente solo ve los suyos) |
| `PATCH /pedidos/<id>/estado` | mesero, administrador |
| `POST /reservas`, `GET /reservas`, `DELETE /reservas/<id>` | sesión |
| `GET /caja/reporte`, `POST /caja/cierre`, `GET /caja/cierres` | administrador |

## Documentación

- `docs/estructura_base_datos.md` — modelo de datos
- `docs/manual_despliegue.md` — despliegue paso a paso
- `docs/convenciones_codigo.md` — estructura de carpetas y convenciones de código
- `docs/versionado_y_cambios.md` — versionado, ramas y gestión de cambios después de la línea base
- `CHANGELOG.md` — historial de cambios incluidos en la línea base

## Alcance y limitaciones de la línea base

- No incluye interfaz gráfica: la línea base es el servicio (API) y su base de datos.
- El seguimiento de pedidos se hace consultando el estado (sondeo); no hay notificaciones en tiempo real.
- No hay facturación electrónica ni integración con pasarelas de pago.
- No se configuró integración continua; Jenkins queda previsto como herramienta futura.
