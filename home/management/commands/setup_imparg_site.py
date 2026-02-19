"""
Configura el sitio Wagtail para imparg.org.
Ejecutar una vez después de las migraciones (o al cambiar de dominio):

  python manage.py setup_imparg_site

Actualiza el Site por defecto para hostname imparg.org, puerto 443 (HTTPS).
"""
from django.core.management.base import BaseCommand
from wagtail.models import Site, Page


class Command(BaseCommand):
    help = "Configura el sitio para imparg.org (hostname y URL base)."

    def handle(self, *args, **options):
        # Root page: la primera página de tipo HomePage a nivel raíz
        from home.models import HomePage
        root_page = Page.objects.type(HomePage).filter(depth=2).first()
        if not root_page:
            self.stderr.write(self.style.ERROR("No se encontró ninguna HomePage. Ejecutá las migraciones primero."))
            return

        site = Site.objects.filter(is_default_site=True).first()
        if not site:
            site = Site(hostname="localhost", port=80, root_page=root_page, is_default_site=True)

        site.hostname = "imparg.org"
        site.port = 443
        site.site_name = "IMPA"
        site.root_page = root_page
        site.is_default_site = True
        site.save()

        self.stdout.write(self.style.SUCCESS(
            f"Sitio configurado: {site.hostname}:{site.port} → {site.site_name} (root: {root_page.title})"
        ))
