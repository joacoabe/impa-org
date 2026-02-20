"""Middleware: corrige Host duplicado, fuerza HTTPS y evita 403 por Referer faltante."""


class LogHostMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.META.get("HTTP_HOST", "")
        # El proxy a veces reenvía Host duplicado (ej. "imparg.org,imparg.org"); Django rechaza con 400
        if host and "," in host:
            request.META["HTTP_HOST"] = host.split(",")[0].strip()
            host = request.META["HTTP_HOST"]
        proto = request.META.get("HTTP_X_FORWARDED_PROTO", "")
        if proto and "," in proto:
            request.META["HTTP_X_FORWARDED_PROTO"] = proto.split(",")[0].strip()
            proto = request.META["HTTP_X_FORWARDED_PROTO"]
        # En impa.ar e imparg.org el sitio se sirve siempre por HTTPS. Si el proxy no reenvía
        # X-Forwarded-Proto (o envía "http"), las URLs absolutas salen en http:// y
        # el navegador bloquea (Mixed Content). Forzamos https para estos dominios.
        if host:
            host_clean = host.split(":")[0].lower()
            if host_clean in ("impa.ar", "www.impa.ar", "imparg.org", "www.imparg.org"):
                request.META["HTTP_X_FORWARDED_PROTO"] = "https"
        # Si no hay Referer pero el Host es nuestro, añadimos Referer para que CSRF no devuelva 403
        # (p. ej. al abrir el sitio desde un enlace externo o por IP que no envía Referer)
        if not request.META.get("HTTP_REFERER") and host:
            scheme = "https" if request.META.get("HTTP_X_FORWARDED_PROTO") == "https" else request.scheme
            request.META["HTTP_REFERER"] = f"{scheme}://{host}/"
        return self.get_response(request)
