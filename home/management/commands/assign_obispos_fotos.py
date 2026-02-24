"""
Asigna las fotos de obispos (por nombre de archivo/título) a las autoridades
(Mardones, Ojeda, Alvarez, etc.) y las quita del carrusel de la Home si estaban.

Uso:
  python manage.py assign_obispos_fotos
"""
from django.core.management.base import BaseCommand
from wagtail.images import get_image_model
from wagtail.models import Page

from home.models import HomePage, Autoridad

# (patrón en título de imagen, patrón en nombre de Autoridad)
OBISPOS_A_ASIGNAR = [
    ("mardones", "Mardones"),
    ("ojeda", "Ojeda"),
    ("alvarez", "Alvarez"),
]


def find_image_by_title_pattern(ImageModel, pattern):
    """Devuelve la primera imagen cuyo título contenga pattern (case-insensitive)."""
    return ImageModel.objects.filter(title__icontains=pattern).first()


def main(command):
    Image = get_image_model()
    ids_to_remove_from_carousel = []

    for img_pattern, nom_pattern in OBISPOS_A_ASIGNAR:
        img = find_image_by_title_pattern(Image, img_pattern)
        aut = Autoridad.objects.filter(nombre__icontains=nom_pattern).first()
        if not img:
            command.stderr.write(command.style.WARNING(f'No se encontró imagen con "{img_pattern}" en el título.'))
            continue
        if not aut:
            command.stderr.write(command.style.ERROR(f'No se encontró autoridad con "{nom_pattern}" en el nombre.'))
            continue
        aut.foto = img
        aut.save()
        command.stdout.write(command.style.SUCCESS(f"  Foto asignada a {aut.nombre}."))
        ids_to_remove_from_carousel.append(img.id)

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
    help = "Asigna fotos de obispos (mardones, ojeda, alvarez, etc.) a Autoridades y las quita del carrusel si estaban."

    def handle(self, *args, **options):
        main(self)
