from django.urls import path
from home import views

app_name = "home"

urlpatterns = [
    path("entrar/", views.entrar, name="entrar"),
    path("iglesias/<slug:slug>/sitio/", views.iglesia_sitio, name="iglesia_sitio"),
    path("iglesias/<slug:slug>/sitio/editar/", views.iglesia_sitio_editar, name="iglesia_sitio_editar"),
    path("iglesias/<slug:slug>/sitio/subir-foto/", views.iglesia_sitio_subir_foto, name="iglesia_sitio_subir_foto"),
    path("auth/intranet/", views.auth_intranet, name="auth_intranet"),
    path("auth/intranet/logout/", views.auth_intranet_logout, name="auth_intranet_logout"),
]
