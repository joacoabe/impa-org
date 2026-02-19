# Nginx para imparg.org

Este proyecto usa una **VM proxy** que recibe todo el tráfico de imparg.org. La app Wagtail corre en otra VM (192.168.1.51) en el puerto 5010.

## Config del proxy (tu VM proxy)

- **Archivo de referencia:** `imparg.org.proxy.conf`
- Va en el **proxy**, no en la máquina donde corre la app:
  - Copiar a `/etc/nginx/sites-available/imparg.org`
  - Enlazar en `sites-enabled/`, probar con `nginx -t` y recargar.

En esa config:
- `/` → 192.168.1.51:5010 (sitio IMPA)
- `/impa-static/` → 192.168.1.51:5010/impa-static/
- `/media/` → 192.168.1.51:5010/media/
- `/intranet/` → 192.168.1.51:5020

## App en la VM 192.168.1.51 (IMPA)

La app está preparada para ese proxy:

- **STATIC_URL** = `/impa-static/` (enlaces a CSS/JS apuntan ahí; el proxy los envía al 5010).
- **WhiteNoise** sirve los estáticos en 5010 bajo `/impa-static/` (no hace falta Nginx en la VM de la app).

En la VM de la app solo tenés que tener levantado Gunicorn en el puerto 5010 (`./start.sh` o `bash start.sh`). No hace falta Nginx en esa VM.

## Si en el futuro usás Nginx en la VM de la app

`imparg.org.conf` es un ejemplo para el caso “todo en la misma máquina” (Nginx + app en el mismo host). Con el proxy actual no lo usás en la VM IMPA.
