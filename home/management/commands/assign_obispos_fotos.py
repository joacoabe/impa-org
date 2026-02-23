"""
Asigna las fotos de obispos (por nombre de archivo/título) a las autoridades
Mardones y Ojeda, y las quita del carrusel de la Home si estaban ahí.

Uso:
  python manage.py assign_obispos_fotos
"""
from django.core.management.base import BaseCommand
from wagtail.images import get_image_model
from wagtail.models import Page

from home.models import HomePage, Autoridad


def find_image_by_title_pattern(ImageModel, pattern):
    """Devuelve la primera imagen cuyo título contenga pattern (case-insensitive)."""
    return ImageModel.objects.filter(title__icontains=pattern).first()


def main(command):
    Image = get_image_model()

    # Buscar imágenes por título (Wagtail suele poner el nombre del archivo sin extensión)
    img_mardones = find_image_by_title_pattern(Image, "mardones")
    img_ojeda = find_image_by_title_pattern(Image, "ojeda")

    if not img_mardones:
        command.stderr.write(command.style.WARNING('No se encontró ninguna imagen con "mardones" en el título.'))
    if not img_ojeda:
        command.stderr.write(command.style.WARNING('No se encontró ninguna imagen con "ojeda" en el título.'))

    # Autoridades por nombre (Mardones = actual, Ojeda = anterior)
    aut_mardones = Autoridad.objects.filter(nombre__icontains="Mardones").first()
    aut_ojeda = Autoridad.objects.filter(nombre__icontains="Ojeda").first()

    if not aut_mardones:
        command.stderr.write(command.style.ERROR('No se encontró autoridad con "Mardones" (ej. Gustavo Mardones Zapata).'))
    if not aut_ojeda:
        command.stderr.write(command.style.ERROR('No se encontró autoridad con "Ojeda" (ej. Germán Ojeda Arteaga).'))

    ids_to_remove_from_carousel = []

    if img_mardones and aut_mardones:
        aut_mardones.foto = img_mardones
        aut_mardones.save()
        command.stdout.write(command.style.SUCCESS(f"  Foto asignada a {aut_mardones.nombre}."))
        ids_to_remove_from_carousel.append(img_mardones.id)

    if img_ojeda and aut_ojeda:
        aut_ojeda.foto = img_ojeda
        aut_ojeda.save()
        command.stdout.write(command.style.SUCCESS(f"  Foto asignada a {aut_ojeda.nombre}."))
        ids_to_remove_from_carousel.append(img_ojeda.id)

    # Quitar estas imágenes del carrusel de la Home si están
    root = Page.objects.type(HomePage).filter(depth=2).first()
    if not root:
        return
    home = root.specific
    if not home.carousel or not ids_to_remove_from_carousel:
        command.stdout.write(command.style.SUCCESS("\nListo. Las fotos no estaban en el carrusel o el carrusel está vacío."))
        return

    field = HomePage._meta.get_field("carousel")
    stream_block = field.stream_block
    new_blocks = []
    removed = 0
    for block in home.carousel:
        if block.block_type == "image" and block.value:
            img_id = getattr(block.value, "id", None)
            if img_id is not None and img_id in ids_to_remove_from_carousel:
                removed += 1
                continue
        new_blocks.append((block.block_type, block.value))
    if removed:
        home.carousel = stream_block.to_python(new_blocks)
        home.save()
        command.stdout.write(command.style.SUCCESS(f"\nSe quitaron {removed} foto(s) del carrusel de la portada."))
    command.stdout.write(command.style.SUCCESS("\nListo."))


class Command(BaseCommand):
    help = "Asigna fotos de obispos (mardones, ojeda) a Autoridades y las quita del carrusel si estaban."

    def handle(self, *args, **options):
        main(self)
