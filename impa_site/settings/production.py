from .base import *

DEBUG = False

# Producción: obligatorio definir SECRET_KEY y ALLOWED_HOSTS en .env
SECRET_KEY = os.environ.get("SECRET_KEY")
if not SECRET_KEY:
    raise ValueError("SECRET_KEY debe estar definido en producción (archivo .env)")

# Hosts permitidos: dominio público + con puerto (por si el proxy reenvía Host: imparg.org:443)
_default_hosts = (
    "imparg.org,www.imparg.org,"
    "imparg.org:443,www.imparg.org:443,"
    "localhost,127.0.0.1,192.168.1.51,"
    "localhost:5010,127.0.0.1:5010,192.168.1.51:5010"
)
ALLOWED_HOSTS = [
    h.strip() for h in os.environ.get("ALLOWED_HOSTS", _default_hosts).split(",") if h.strip()
]

# URL del sitio en producción
WAGTAILADMIN_BASE_URL = os.environ.get("WAGTAILADMIN_BASE_URL", "https://imparg.org")

# Detrás del proxy: Nginx envía Host: imparg.org; confiar en ese Host (no en X-Forwarded-Host si no está)
USE_X_FORWARDED_HOST = False
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# Estáticos: el proxy reenvía /impa-static/ a esta app (5010). No usar /static/ (el proxy lo manda a FileBrowser).
STATIC_URL = os.environ.get("STATIC_URL", "/impa-static/")

# WhiteNoise sirve /impa-static/ cuando el proxy envía la petición a 5010 (cache-busting con manifest)
STORAGES["staticfiles"]["BACKEND"] = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Log de errores a consola (journalctl -u impaorg muestra el traceback del 500)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django.request": {
            "handlers": ["console"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}

try:
    from .local import *
except ImportError:
    pass
