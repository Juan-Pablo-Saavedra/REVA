# Estructura de carpetas y convenciones de código

## Estructura

```
REVA/
├── sigr/                 Código de la aplicación (un módulo por funcionalidad)
│   ├── __init__.py       Fábrica de la aplicación y comandos de consola
│   ├── db.py             Conexión a SQLite
│   ├── util.py           Validaciones y respuestas comunes
│   ├── auth.py           Autenticación y roles
│   ├── menu.py           Menú digital
│   ├── mesas.py          Mesas
│   ├── pedidos.py        Pedidos
│   ├── reservas.py       Reservas
│   └── caja.py           Cierre de caja y reportes
├── database/schema.sql   Esquema de la base de datos
├── tests/                Pruebas (una por módulo + integración)
├── docs/                 Documentación técnica
├── .github/              Plantillas de issues y de pull requests
├── run.py                Punto de entrada de desarrollo
├── requirements.txt      Dependencias
├── CHANGELOG.md  LICENSE.txt  README.md
```

## Convenciones de código

- Python 3.11+, estilo PEP 8, sangría de 4 espacios y líneas de hasta unos 100 caracteres.
- Nombres de funciones y variables en `snake_case`; nombres del dominio en español (`pedido`, `reserva`).
- Cada módulo de negocio es un *Blueprint* de Flask con su propio prefijo de ruta.
- Las respuestas de error son siempre JSON con la forma `{"error": "..."}`; los errores de validación
  añaden `errores` con un mensaje por campo y usan el código 422.
- Códigos HTTP: 201 al crear, 204 al eliminar, 400 si el cuerpo no es JSON, 401 sin sesión,
  403 sin permiso, 404 si no existe, 409 en conflictos de negocio (duplicados, transiciones inválidas).
- Las consultas SQL usan siempre parámetros (`?`), nunca concatenación de datos del usuario.
- Los secretos (claves, tokens) se leen de variables de entorno; no se guardan en el repositorio.
- Cada función nueva de un módulo debe llevar pruebas en `tests/`.
