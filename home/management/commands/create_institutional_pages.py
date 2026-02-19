"""
Crea las cuatro páginas institucionales bajo la HomePage raíz:
Historia, Visión, Doctrina, Autoridades.

Ejecutar una vez (o cuando falten páginas):

  python manage.py create_institutional_pages

No duplica: si ya existe una página con ese slug, la omite.
"""
from django.core.management.base import BaseCommand
from wagtail.models import Page

from home.models import HomePage, InstitutionalPage


TIPO_SLUGS = [
    ("historia", "Historia"),
    ("vision", "Visión"),
    ("doctrina", "Doctrina"),
    ("autoridades", "Autoridades"),
]


class Command(BaseCommand):
    help = "Crea las páginas institucionales (Historia, Visión, Doctrina, Autoridades) bajo Home."

    def handle(self, *args, **options):
        root = Page.objects.type(HomePage).filter(depth=2).first()
        if not root:
            self.stderr.write(self.style.ERROR("No se encontró HomePage raíz. Ejecutá las migraciones."))
            return

        root = root.specific
        created = 0
        for tipo, title in TIPO_SLUGS:
            if root.get_children().filter(slug=tipo).exists():
                self.stdout.write(f"  Ya existe: {title} (/ {tipo} /)")
                continue
            page = InstitutionalPage(
                title=title,
                tipo=tipo,
                body=[],
            )
            root.add_child(instance=page)
            created += 1
            self.stdout.write(self.style.SUCCESS(f"  Creada: {title} (/ {tipo} /)"))

        if created:
            self.stdout.write(self.style.SUCCESS(f"\nListo. {created} página(s) creada(s)."))
        else:
            self.stdout.write("\nNo se creó ninguna página nueva (todas ya existían).")
