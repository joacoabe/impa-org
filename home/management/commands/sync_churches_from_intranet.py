"""
Sincroniza las fichas de iglesias desde la API pública de la intranet.

Configuración (variables de entorno):
  INTRANET_CHURCHES_API_URL  — URL del endpoint (ej. https://imparg.org/intranet/api/v1/public/churches)
  INTRANET_CHURCHES_API_KEY  — Opcional; si la API lo exige, header X-API-Key

Ejecutar:
  python manage.py sync_churches_from_intranet

Por cada iglesia en la respuesta:
  - Si existe una IglesiaPage con el mismo intranet_id, se actualiza.
  - Si no, se crea una nueva como hija de la página "Iglesias".

Formato esperado de la API: {"data": [{"id", "name", "latitude", "longitude", "province", "address", "city", "pastor", "pastora"}, ...]}
"""
import os
import re
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand
from wagtail.models import Page

from home.models import IglesiasIndexPage, IglesiaPage


def slugify_unique(base_slug, existing_slugs):
    """Devuelve base_slug o base_slug-N para que sea único."""
    slug = re.sub(r"[^\w\s-]", "", base_slug).strip().lower()
    slug = re.sub(r"[-\s]+", "-", slug) or "iglesia"
    if slug not in existing_slugs:
        return slug
    n = 1
    while f"{slug}-{n}" in existing_slugs:
        n += 1
    return f"{slug}-{n}"


def format_pastor(obj):
    if not obj:
        return ""
    first = (obj.get("first_name") or "").strip()
    last = (obj.get("last_name") or "").strip()
    return " ".join(filter(None, [first, last]))


class Command(BaseCommand):
    help = "Sincroniza iglesias desde la API pública de la intranet (INTRANET_CHURCHES_API_URL)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Solo mostrar qué se haría, sin crear ni actualizar.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        api_url = os.environ.get("INTRANET_CHURCHES_API_URL") or getattr(
            settings, "INTRANET_CHURCHES_API_URL", None
        )
        if not api_url:
            self.stderr.write(
                self.style.ERROR(
                    "Definí INTRANET_CHURCHES_API_URL (env o settings). "
                    "Ej: https://imparg.org/intranet/api/v1/public/churches"
                )
            )
            return

        headers = {}
        api_key = os.environ.get("INTRANET_CHURCHES_API_KEY") or getattr(
            settings, "INTRANET_CHURCHES_API_KEY", None
        )
        if api_key:
            headers["X-API-Key"] = api_key

        try:
            import requests
            resp = requests.get(api_url, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()
        except ImportError:
            self.stderr.write(self.style.ERROR("Instalá 'requests': pip install requests"))
            return
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error al llamar a la API: {e}"))
            return

        items = data.get("data") or []
        if not items:
            self.stdout.write(self.style.WARNING("La API no devolvió iglesias (data vacío)."))
            return

        parent = Page.objects.type(IglesiasIndexPage).filter(slug="iglesias").live().first()
        if not parent:
            self.stderr.write(
                self.style.ERROR("No se encontró la página Iglesias (IglesiasIndexPage con slug=iglesias).")
            )
            return
        parent = parent.specific

        existing_by_id = {
            p.intranet_id: p
            for p in IglesiaPage.objects.filter(intranet_id__isnull=False)
            .select_related()
        }
        existing_slugs = set(
            parent.get_children().values_list("slug", flat=True)
        )

        created = 0
        updated = 0
        for item in items:
            intranet_id = item.get("id")
            name = (item.get("name") or "").strip() or "Iglesia"
            lat = item.get("latitude")
            lon = item.get("longitude")
            province = (item.get("province") or "").strip() or ""
            address = (item.get("address") or "").strip() or ""
            city = (item.get("city") or item.get("ciudad") or "").strip() or ""
            pastor = format_pastor(item.get("pastor"))
            pastora = format_pastor(item.get("pastora"))
            pastor_text = " / ".join(filter(None, [pastor, pastora])) if (pastor or pastora) else ""

            if dry_run:
                if intranet_id and intranet_id in existing_by_id:
                    self.stdout.write(f"  [actualizar] id={intranet_id} {name}")
                    updated += 1
                else:
                    self.stdout.write(f"  [crear] {name} (lat={lat}, lon={lon})")
                    created += 1
                continue

            if intranet_id and intranet_id in existing_by_id:
                page = existing_by_id[intranet_id].specific
                page.title = name
                page.nombre = name
                page.provincia = province
                page.direccion = address
                page.ciudad = city
                page.pastor_nombre = pastor_text
                if lat is not None and lon is not None:
                    page.latitud = Decimal(str(lat))
                    page.longitud = Decimal(str(lon))
                page.save_revision().publish()
                updated += 1
                self.stdout.write(self.style.SUCCESS(f"  Actualizada: {name}"))
            else:
                slug = slugify_unique(name, existing_slugs)
                existing_slugs.add(slug)
                page = IglesiaPage(
                    title=name,
                    nombre=name,
                    intranet_id=intranet_id,
                    provincia=province,
                    direccion=address,
                    ciudad=city,
                    pastor_nombre=pastor_text,
                )
                if lat is not None and lon is not None:
                    page.latitud = Decimal(str(lat))
                    page.longitud = Decimal(str(lon))
                parent.add_child(instance=page)
                page.save_revision().publish()
                created += 1
                self.stdout.write(self.style.SUCCESS(f"  Creada: {name}"))

        if dry_run:
            self.stdout.write(self.style.SUCCESS(f"\nDry-run: {created} a crear, {updated} a actualizar."))
        else:
            self.stdout.write(self.style.SUCCESS(f"\nListo. {created} creadas, {updated} actualizadas."))
