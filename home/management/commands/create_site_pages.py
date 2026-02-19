"""
Crea bajo la HomePage raíz las páginas de sección:
Iglesias, Noticias, Recursos, Radios, Contacto, Mapa.

Ejecutar una vez (o cuando falten):

  python manage.py create_site_pages

No duplica: si ya existe una página con ese slug, la omite.

Para publicar páginas que ya existan pero estén en borrador:
  python manage.py create_site_pages --publish-existing
"""
from django.core.management.base import BaseCommand
from wagtail.models import Page

from home.models import (
    HomePage,
    IglesiasIndexPage,
    NoticiasIndexPage,
    RecursosIndexPage,
    RadiosIndexPage,
    ContactoPage,
    MapaPage,
)


# (slug, título, clase del modelo)
PAGINAS = [
    ("iglesias", "Iglesias", IglesiasIndexPage),
    ("noticias", "Noticias", NoticiasIndexPage),
    ("recursos", "Recursos", RecursosIndexPage),
    ("radios", "Radios", RadiosIndexPage),
    ("contacto", "Contacto", ContactoPage),
    ("mapa", "Mapa", MapaPage),
]


class Command(BaseCommand):
    help = "Crea las páginas Iglesias, Noticias, Recursos, Radios, Contacto y Mapa bajo Home."

    def add_arguments(self, parser):
        parser.add_argument(
            "--publish-existing",
            action="store_true",
            help="Publicar hijos de la Home que estén en borrador.",
        )

    def handle(self, *args, **options):
        root = Page.objects.type(HomePage).filter(depth=2).first()
        if not root:
            self.stderr.write(self.style.ERROR("No se encontró HomePage raíz. Ejecutá las migraciones."))
            return

        root = root.specific
        created = 0
        for slug, title, model_class in PAGINAS:
            child = root.get_children().filter(slug=slug).first()
            if child:
                if options.get("publish_existing") and not child.live:
                    rev = child.get_latest_revision()
                    if rev:
                        rev.publish()
                        self.stdout.write(self.style.SUCCESS(f"  Publicada: {title} (/{slug}/)"))
                else:
                    self.stdout.write(f"  Ya existe: {title} (/{slug}/)")
                continue
            page = model_class(title=title)
            if hasattr(page, "intro"):
                page.intro = ""
            if hasattr(page, "body") and page.body is None:
                page.body = []
            root.add_child(instance=page)
            page.save_revision().publish()
            created += 1
            self.stdout.write(self.style.SUCCESS(f"  Creada y publicada: {title} (/{slug}/)"))

        if created:
            self.stdout.write(self.style.SUCCESS(f"\nListo. {created} página(s) creada(s)."))
        elif not options.get("publish_existing"):
            self.stdout.write("\nNo se creó ninguna página nueva (todas ya existían).")
