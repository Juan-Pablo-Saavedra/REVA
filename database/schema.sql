-- Esquema de la base de datos del SIGR (SQLite).
-- Los valores monetarios se guardan como enteros en pesos colombianos (COP).

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS usuarios (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre      TEXT NOT NULL,
    correo      TEXT NOT NULL UNIQUE,
    clave_hash  TEXT NOT NULL,
    rol         TEXT NOT NULL CHECK (rol IN ('cliente', 'mesero', 'administrador')),
    creado_en   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS categorias (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre  TEXT NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS platos (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    categoria_id  INTEGER NOT NULL REFERENCES categorias(id),
    nombre        TEXT NOT NULL,
    descripcion   TEXT NOT NULL DEFAULT '',
    precio        INTEGER NOT NULL CHECK (precio > 0),
    disponible    INTEGER NOT NULL DEFAULT 1 CHECK (disponible IN (0, 1)),
    UNIQUE (categoria_id, nombre)
);

CREATE TABLE IF NOT EXISTS mesas (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    numero     INTEGER NOT NULL UNIQUE,
    capacidad  INTEGER NOT NULL CHECK (capacidad > 0)
);

CREATE TABLE IF NOT EXISTS pedidos (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id     INTEGER NOT NULL REFERENCES usuarios(id),
    mesa_id        INTEGER REFERENCES mesas(id),
    estado         TEXT NOT NULL DEFAULT 'pendiente'
                   CHECK (estado IN ('pendiente', 'en_preparacion', 'listo',
                                     'entregado', 'pagado', 'cancelado')),
    total          INTEGER NOT NULL CHECK (total >= 0),
    fecha          TEXT NOT NULL,
    creado_en      TEXT NOT NULL,
    actualizado_en TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pedido_items (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    pedido_id        INTEGER NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
    plato_id         INTEGER NOT NULL REFERENCES platos(id),
    cantidad         INTEGER NOT NULL CHECK (cantidad > 0),
    precio_unitario  INTEGER NOT NULL CHECK (precio_unitario > 0)
);

CREATE TABLE IF NOT EXISTS reservas (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id  INTEGER NOT NULL REFERENCES usuarios(id),
    mesa_id     INTEGER NOT NULL REFERENCES mesas(id),
    fecha       TEXT NOT NULL,
    hora        TEXT NOT NULL,
    personas    INTEGER NOT NULL CHECK (personas > 0),
    estado      TEXT NOT NULL DEFAULT 'activa' CHECK (estado IN ('activa', 'cancelada')),
    creado_en   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS cierres_caja (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha         TEXT NOT NULL UNIQUE,
    total_ventas  INTEGER NOT NULL,
    num_pedidos   INTEGER NOT NULL,
    cerrado_por   INTEGER NOT NULL REFERENCES usuarios(id),
    cerrado_en    TEXT NOT NULL
);
