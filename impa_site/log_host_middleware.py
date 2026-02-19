"""Middleware: corrige Host duplicado y fuerza HTTPS para imparg.org (evita Mixed Content)."""


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
        # En imparg.org el sitio se sirve siempre por HTTPS. Si el proxy no reenvía
        # X-Forwarded-Proto (o envía "http"), las URLs absolutas salen en http:// y
        # el navegador bloquea (Mixed Content). Forzamos https para este dominio.
        if host:
            host_clean = host.split(":")[0].lower()
            if host_clean in ("imparg.org", "www.imparg.org"):
                request.META["HTTP_X_FORWARDED_PROTO"] = "https"
        return self.get_response(request)
