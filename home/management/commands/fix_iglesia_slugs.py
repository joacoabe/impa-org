"""
Actualiza los slugs de las páginas de iglesias para que conserven ñ y acentos.

Las iglesias creadas con una versión antigua del sync tienen slugs como "cordoba"
o "anelo". Este comando los reemplaza por "córdoba", "añelo", etc., para que
/iglesias/córdoba/ y /iglesias/añelo/ funcionen con Wagtail.

Ejecutar:
  python manage.py fix_iglesia_slugs
  python manage.py fix_iglesia_slugs --dry-run  # solo mostrar cambios
"""
import re
import unicodedata

from django.core.management.base import BaseCommand
from wagtail.models import Page

from home.models import IglesiasIndexPage, IglesiaPage


def slug_from_title(title):
    """Slug que preserva ñ y acentos (misma lógica que sync_churches_from_intranet)."""
    if not title:
        return "iglesia"
    s = unicodedata.normalize("NFC", title)
    s = re.sub(r"[^\w\s-]", "", s, flags=re.UNICODE).strip().lower()
    s = re.sub(r"[-\s]+", "-", s) or "iglesia"
    return s


class Command(BaseCommand):
    help = "Actualiza slugs de IglesiaPage para conservar ñ y acentos (córdoba, añelo, etc.)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Solo mostrar qué se cambiaría, sin guardar.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        index = IglesiasIndexPage.objects.live().first()
        if not index:
            self.stderr.write(self.style.ERROR("No se encontró la página índice Iglesias."))
            return

        children = list(
            Page.objects.child_of(index).type(IglesiaPage).live().order_by("slug")
        )
        if not children:
            self.stdout.write("No hay iglesias publicadas.")
            return

        # Calcular slug deseado por título y resolver colisiones
        desired = {}
        used = set()
        for page in children:
            want = slug_from_title(page.title)
            if want in used:
                n = 1
                while f"{want}-{n}" in used:
                    n += 1
                want = f"{want}-{n}"
            used.add(want)
            desired[page.pk] = want

        updated = 0
        for page in children:
            page = page.specific
            current = page.slug
            want = desired[page.pk]
            if current == want:
                continue
            if dry_run:
                self.stdout.write(f"  [cambiaría] “{page.title}”: {current!r} → {want!r}")
            else:
                page.slug = want
                page.save_revision().publish()
                self.stdout.write(self.style.SUCCESS(f"  Actualizado: “{page.title}” → /iglesias/{want}/"))
            updated += 1

        if dry_run and updated:
            self.stdout.write(self.style.WARNING(f"\nDry-run: {updated} slugs se actualizarían. Ejecutá sin --dry-run para aplicar."))
        elif updated:
            self.stdout.write(self.style.SUCCESS(f"\nListo. {updated} slug(s) actualizados."))
        else:
            self.stdout.write("No había slugs que actualizar.")
