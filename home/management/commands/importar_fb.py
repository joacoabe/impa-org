import re
from datetime import datetime
from time import mktime

import feedparser
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from home.models import NoticiaPage, NoticiasIndexPage


def _extraer_imagen_desde_entry(entry):
    """Extrae la URL de la imagen de una entrada del feed (varias fuentes posibles)."""
    # 1. media_content (Media RSS)
    if getattr(entry, "media_content", None) and len(entry.media_content) > 0:
        url = entry.media_content[0].get("url") or entry.media_content[0].get("href")
        if url:
            return url
    # 2. media_thumbnail
    if getattr(entry, "media_thumbnail", None) and len(entry.media_thumbnail) > 0:
        url = entry.media_thumbnail[0].get("url") or entry.media_thumbnail[0].get("href")
        if url:
            return url
    # 3. enclosures (RSS 2.0: type image/* o cualquier enclosure)
    if getattr(entry, "enclosures", None):
        for enc in entry.enclosures:
            url = enc.get("href") or enc.get("url")
            if not url:
                continue
            type_ = (enc.get("type") or "").lower()
            if "image" in type_ or not type_:
                return url
        if entry.enclosures:
            url = entry.enclosures[0].get("href") or entry.enclosures[0].get("url")
            if url:
                return url
    # 4. Primera <img> en summary o content
    for field in ("summary", "content", "description"):
        html = getattr(entry, field, None)
        if isinstance(html, str) and "img" in html.lower():
            match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', html, re.I)
            if match:
                return match.group(1).strip()
        elif hasattr(html, "value") and isinstance(html.value, str):
            match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', html.value, re.I)
            if match:
                return match.group(1).strip()
    return ""


class Command(BaseCommand):
    help = "Importa noticias de Facebook de la Iglesia vía RSS.app"

    def handle(self, *args, **options):
        RSS_URL = "https://rss.app/feeds/DpG11mcZkMgvGykq.xml"

        parent = NoticiasIndexPage.objects.live().first()
        if not parent:
            self.stderr.write(
                self.style.ERROR(
                    "Error: No se encontró una página 'Noticias Index' publicada en Wagtail."
                )
            )
            return

        try:
            feed = feedparser.parse(RSS_URL)
        except Exception as e:
            self.stderr.write(
                self.style.ERROR(f"Error al obtener el feed RSS: {str(e)}")
            )
            return

        count_new = 0
        count_actualizadas = 0
        for entry in feed.entries:
            fb_id = entry.get("id") or entry.get("link") or ""
            if not fb_id:
                continue

            # Imagen: varias fuentes (media_content, media_thumbnail, enclosures, <img> en HTML)
            url_foto = _extraer_imagen_desde_entry(entry) or None

            existing = NoticiaPage.objects.filter(facebook_id=fb_id).first()
            if existing:
                # Actualizar imagen si antes no tenía y ahora sí
                if url_foto and not existing.url_imagen_fb:
                    existing.url_imagen_fb = url_foto
                    existing.save_revision().publish()
                    count_actualizadas += 1
                continue

            # Fecha: published_parsed puede no existir en algunos feeds
            if getattr(entry, "published_parsed", None):
                dt = datetime.fromtimestamp(mktime(entry.published_parsed))
                fecha = dt.date()
            else:
                fecha = datetime.now().date()

            titulo = (entry.get("title") or "Noticia de Facebook")[:60].strip()
            summary = entry.get("summary") or ""

            nueva = NoticiaPage(
                title=titulo,
                slug=slugify(f"fb-{str(fb_id)[-8:]}"),
                date=fecha,
                body=summary,
                intro=(summary[:180] + "...") if len(summary) > 180 else summary,
                facebook_id=fb_id,
                url_imagen_fb=url_foto,
                autor="Facebook IMPA",
            )
            parent.add_child(instance=nueva)
            nueva.save_revision().publish()
            count_new += 1

        msg = f"Proceso terminado. Se importaron {count_new} noticias nuevas."
        if count_actualizadas:
            msg += f" Se actualizaron {count_actualizadas} con imagen."
        self.stdout.write(self.style.SUCCESS(msg))
