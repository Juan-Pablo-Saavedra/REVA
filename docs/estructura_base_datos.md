# Estructura de la base de datos

Motor: SQLite. El esquema completo está en `database/schema.sql` y se crea con
`flask --app sigr init-db`. Los valores monetarios son enteros en pesos colombianos (COP).

## Tablas

| Tabla | Propósito | Columnas principales |
|---|---|---|
| `usuarios` | Cuentas del sistema | `id`, `nombre`, `correo` (único), `clave_hash`, `rol` (`cliente`/`mesero`/`administrador`) |
| `categorias` | Agrupan los platos del menú | `id`, `nombre` (único) |
| `platos` | Platos del menú digital | `id`, `categoria_id`, `nombre`, `descripcion`, `precio`, `disponible` |
| `mesas` | Mesas del salón | `id`, `numero` (único), `capacidad` |
| `pedidos` | Cabecera de cada pedido | `id`, `usuario_id`, `mesa_id`, `estado`, `total`, `fecha` |
| `pedido_items` | Líneas de cada pedido | `pedido_id`, `plato_id`, `cantidad`, `precio_unitario` |
| `reservas` | Reservas de mesa | `id`, `usuario_id`, `mesa_id`, `fecha`, `hora`, `personas`, `estado` |
| `cierres_caja` | Un registro por día cerrado | `fecha` (único), `total_ventas`, `num_pedidos`, `cerrado_por` |

## Relaciones

- `categorias` 1—N `platos`
- `usuarios` 1—N `pedidos` y 1—N `reservas`
- `mesas` 1—N `pedidos` (opcional) y 1—N `reservas`
- `pedidos` 1—N `pedido_items`; cada ítem apunta a un `plato`
- `usuarios` 1—N `cierres_caja` (quién cerró)

## Decisiones de diseño

- `pedido_items.precio_unitario` guarda el precio del plato al momento del pedido, de modo que un
  cambio posterior en el menú no altera pedidos ya registrados ni los reportes.
- `pedidos.estado` está restringido por `CHECK` a: `pendiente`, `en_preparacion`, `listo`,
  `entregado`, `pagado`, `cancelado`. Las transiciones válidas se controlan en `sigr/pedidos.py`.
- Las claves se almacenan como hash (`werkzeug.security`); nunca en texto plano.
- Las claves foráneas se activan con `PRAGMA foreign_keys = ON`.
