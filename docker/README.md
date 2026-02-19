# Docker (opcional)

No es necesario usar Docker para desarrollar ni desplegar el sitio. El proyecto puede ejecutarse con el entorno virtual y Gunicorn/uWSGI directamente.

Si querés usar Docker:

```bash
# Desde la raíz del proyecto (/home/impa/impa)
docker build -f docker/Dockerfile .
```
