# Manual de despliegue

Esta guía describe cómo poner en marcha la línea base `v1.0.0` en un servidor Linux.
El servidor de desarrollo de Flask (`python run.py`) sirve para pruebas; para producción se usa un
servidor WSGI.

## 1. Preparar el entorno

```bash
sudo apt update && sudo apt install -y python3 python3-venv git
git clone https://github.com/Juan-Pablo-Saavedra/REVA.git
cd REVA
git checkout v1.0.0          # fija el despliegue en la línea base
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt gunicorn
```

## 2. Configurar variables de entorno

| Variable | Descripción |
|---|---|
| `SIGR_SECRET_KEY` | Clave secreta de las sesiones. Obligatoria en producción; no debe subirse al repositorio. |

```bash
export SIGR_SECRET_KEY="$(python3 -c 'import secrets; print(secrets.token_hex(32))')"
```

## 3. Crear la base de datos y el administrador

```bash
flask --app sigr init-db
flask --app sigr crear-admin admin@restaurante.com "Nombre Admin"   # la clave se pide por consola
```

La base queda en `instance/sigr.sqlite` (carpeta ignorada por git).

## 4. Ejecutar

```bash
gunicorn --bind 127.0.0.1:8000 "sigr:create_app()"
curl http://127.0.0.1:8000/salud
```

Se recomienda poner un proxy inverso (por ejemplo Nginx) con HTTPS delante de gunicorn.

## 5. Verificar la instalación

```bash
python -m pytest -q        # deben pasar las 78 pruebas
```

## 6. Copias de seguridad y actualización

- Copia de seguridad: copiar `instance/sigr.sqlite` mientras el servicio está detenido o usar `sqlite3 instance/sigr.sqlite ".backup copia.sqlite"`.
- Actualización: `git fetch --tags`, cambiar a la nueva etiqueta, `pip install -r requirements.txt` y reiniciar el servicio. Antes de actualizar, revisar el `CHANGELOG.md`.
