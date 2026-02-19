#!/usr/bin/env bash
# Arrancar el sitio IMPA en producción (imparg.org), puerto 5010.
# Ejecutar desde la raíz del proyecto: /home/impa/impa
# Si ./start.sh falla, probar: bash start.sh

cd "$(dirname "$0")"
export DJANGO_SETTINGS_MODULE=impa_site.settings.production
export PORT="${PORT:-5010}"

source impa/bin/activate
exec gunicorn impa_site.wsgi:application --bind "0.0.0.0:$PORT" --workers 2 --threads 2
