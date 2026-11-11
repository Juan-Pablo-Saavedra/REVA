# Historial de cambios

Todos los cambios relevantes del SIGR se registran en este archivo.
El formato sigue la idea de "Keep a Changelog" y el versionado es semántico (MAJOR.MINOR.PATCH).

## [Sin publicar]

## [1.0.0-baseline] - 2026-11-11

Primera línea base del SIGR. Reúne los cinco módulos del alcance inicial y su documentación.

### Añadido
- Autenticación con roles `cliente`, `mesero` y `administrador` (`sigr/auth.py`).
- Menú digital: CRUD de categorías y platos y consulta pública (`sigr/menu.py`).
- Pedidos con total calculado en el servidor, precio congelado por ítem y ciclo de estados (`sigr/pedidos.py`).
- Gestión de mesas (`sigr/mesas.py`).
- Reservas por fecha y hora con control de solapamiento (`sigr/reservas.py`).
- Cierre de caja y reporte de ventas diario (`sigr/caja.py`).
- Esquema de base de datos SQLite (`database/schema.sql`) y comandos `init-db` y `crear-admin`.
- 78 pruebas automatizadas, incluida una de integración del flujo diario completo.
- Documentación: README, estructura de la base de datos, manual de despliegue, convenciones de código y política de versionado.
- Plantillas de issues y de pull requests.
- Licencia MIT.

### Limitaciones conocidas
- Sin interfaz gráfica ni notificaciones en tiempo real (el seguimiento de pedidos es por consulta).
- Sin facturación electrónica ni pasarelas de pago.
- Sin integración continua configurada.
