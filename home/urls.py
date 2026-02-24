from django.urls import path, register_converter
from home import views


class UnicodeSlugConverter:
    """Acepta slugs con ñ y acentos (ej. añelo, neuquén-hipódromo)."""
    regex = r"[-\w]+"

    def to_python(self, value):
        return value

    def to_url(self, value):
        return value


register_converter(UnicodeSlugConverter, "unicode_slug")

app_name = "home"

urlpatterns = [
    path("entrar/", views.entrar, name="entrar"),
    path("iglesias/<unicode_slug:slug>/sitio/", views.iglesia_sitio, name="iglesia_sitio"),
    path("iglesias/<unicode_slug:slug>/sitio/editar/", views.iglesia_sitio_editar, name="iglesia_sitio_editar"),
    path("iglesias/<unicode_slug:slug>/sitio/subir-foto/", views.iglesia_sitio_subir_foto, name="iglesia_sitio_subir_foto"),
    path("auth/intranet/", views.auth_intranet, name="auth_intranet"),
    path("auth/intranet/logout/", views.auth_intranet_logout, name="auth_intranet_logout"),
]
