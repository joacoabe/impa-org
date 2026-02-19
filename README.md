# Sitio IMPA (imparg.org)

Sitio web institucional IMPA desarrollado con Wagtail (Django). Listo para servirse en **https://imparg.org** en el **puerto 5010**.

---

## ¿Por qué Gunicorn?

En desarrollo usás `python manage.py runserver` (solo para probar). En **producción** ese servidor no sirve: no está pensado para tráfico real ni para quedarse siempre activo. **Gunicorn** es un servidor WSGI estándar para Django/Wagtail: estable, seguro y pensado para ir detrás de Nginx. Por eso el script `start.sh` usa Gunicorn en el puerto 5010.

Si preferís no usar Gunicorn, podés arrancar en el puerto 5010 con:
```bash
export DJANGO_SETTINGS_MODULE=impa_site.settings.production
python manage.py runserver 0.0.0.0:5010
```
(solo recomendable para pruebas; en producción conviene Gunicorn + Nginx.)

---

## Arrancar en producción (imparg.org)

1. **Variables de entorno**  
   En `.env` deben estar definidas (además de la base de datos):
   - `SECRET_KEY` – clave secreta larga y aleatoria para producción.
   - `ALLOWED_HOSTS=imparg.org,www.imparg.org`
   - Opcional: `WAGTAILADMIN_BASE_URL=https://imparg.org`

2. **Configurar el sitio para imparg.org** (solo la primera vez):
   ```bash
   cd /home/impa/impa
   source impa/bin/activate
   export DJANGO_SETTINGS_MODULE=impa_site.settings.production
   python manage.py setup_imparg_site
   python manage.py collectstatic --noinput
   ```

3. **Dependencias** (si aún no está instalado Gunicorn):
   ```bash
   pip install -r requirements.txt
   ```

4. **Iniciar la aplicación** (puerto 5010):
   ```bash
   cd /home/impa/impa
   ./start.sh
   ```
   Si aparece "cannot execute: required file not found", ejecutá: `bash start.sh`
   O con Gunicorn a mano:
   ```bash
   source impa/bin/activate
   export DJANGO_SETTINGS_MODULE=impa_site.settings.production
   gunicorn impa_site.wsgi:application --bind 0.0.0.0:5010 --workers 2 --threads 2
   ```

5. **Servidor web (Nginx/Apache)**  
   Configurar el proxy hacia `127.0.0.1:5010` y SSL (por ejemplo Certbot) para `imparg.org`.

---

## Desarrollo (runserver)

```bash
cd /home/impa/impa
source impa/bin/activate
python manage.py runserver 0.0.0.0:5010
```

- **Sitio:** http://localhost:5010  
- **Admin:** http://localhost:5010/admin/

---

## Usuario administrador

- **Usuario:** `admin`
- **Email:** `admin@imparg.org`
- **Contraseña por defecto:** `isaias52`

Cambiá la contraseña en producción (Admin → Mi cuenta → Cambiar contraseña).

---

## Base de datos

- **Nombre:** `impaorg`
- **Usuario:** `joacoabe` (todos los privilegios sobre `impaorg`)
- Configuración en `.env`: `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`.

---

## Estructura del proyecto

```
impa/
├── iglesias/          # Carpetas por localidad (Viedma, Chimpay, Neuquén, etc.)
│   ├── chimpay/
│   ├── viedma/
│   └── neuquen/
├── impa/               # Entorno virtual Python
├── impa_site/          # Configuración Wagtail (settings, urls, wsgi)
├── home/               # App Wagtail (HomePage, comando setup_imparg_site)
├── search/
├── manage.py
├── start.sh            # Arranque producción (puerto 5010)
├── .env
├── .env.example
└── docker/             # Docker opcional (ver docker/README.md)
```

---

## Intranet

- **URL:** https://imparg.org/intranet (para futura integración de usuarios).

---

## Subir el proyecto a GitHub (repo `impa-org`)

1. **Crear el repositorio en GitHub**  
   En https://github.com/new creá un repo **vacío** llamado `impa-org` (sin README, sin .gitignore).

2. **En la carpeta del proyecto** (donde está `manage.py`):
   ```bash
   cd /home/impa/impa
   git init
   git add .
   git commit -m "Sitio IMPA (imparg.org) - Wagtail"
   git branch -M main
   git remote add origin https://github.com/joacoabe/impa-org.git
   git push -u origin main
   ```
   Si usás SSH:
   ```bash
   git remote add origin git@github.com:joacoabe/impa-org.git
   ```

3. **Importante:** El archivo `.env` no se sube (está en `.gitignore`). Quien clone el repo debe copiar `.env.example` a `.env` y completar contraseñas y claves.
