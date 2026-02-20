from django.db import models
from wagtail import blocks
from wagtail.admin.panels import FieldPanel, InlinePanel, MultiFieldPanel
from wagtail.fields import RichTextField, StreamField
from wagtail.models import Page
from wagtail.contrib.forms.models import AbstractEmailForm, AbstractFormField
from wagtail.images.blocks import ImageChooserBlock
from wagtail.snippets.models import register_snippet


# ---------- StreamField block definitions (shared) ----------
BODY_BLOCKS = [
    ("paragraph", blocks.RichTextBlock()),
    ("heading", blocks.CharBlock(form_classname="title")),
    ("image", ImageChooserBlock()),
    ("list", blocks.ListBlock(blocks.CharBlock())),
    ("url", blocks.URLBlock()),
]

LINK_BLOCK = blocks.StructBlock([
    ("label", blocks.CharBlock()),
    ("url", blocks.URLBlock()),
], icon="link")


# ---------- HomePage ----------
class HomePage(Page):
    intro = RichTextField(blank=True)
    carousel = StreamField(
        [("image", ImageChooserBlock())],
        blank=True,
        use_json_field=True,
        help_text="Imágenes del carrusel (debajo de las pestañas).",
    )
    body = StreamField(BODY_BLOCKS, blank=True, use_json_field=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
        FieldPanel("carousel"),
        FieldPanel("body"),
    ]

    subpage_types = [
        "home.InstitutionalPage",
        "home.IglesiasIndexPage",
        "home.NoticiasIndexPage",
        "home.RecursosIndexPage",
        "home.RadiosIndexPage",
        "home.ContactoPage",
        "home.MapaPage",
    ]

    def live_children(self):
        """Hijos publicados, para listar en el template."""
        return self.get_children().live()

    def get_ultimas_noticias(self, n=6):
        """Últimas n noticias publicadas (desde la página Noticias)."""
        noticias_page = self.get_children().filter(slug="noticias").live().first()
        if not noticias_page:
            return []
        from home.models import NoticiaPage
        return list(NoticiaPage.objects.child_of(noticias_page.specific).live().order_by("-date")[:n])


# ---------- Fase 2: InstitutionalPage ----------
class InstitutionalPage(Page):
    TIPO_CHOICES = [
        ("historia", "Historia"),
        ("vision", "Visión"),
        ("doctrina", "Doctrina"),
        ("autoridades", "Autoridades"),
    ]
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default="historia")
    body = StreamField(BODY_BLOCKS, blank=True, use_json_field=True)

    content_panels = Page.content_panels + [
        FieldPanel("tipo"),
        FieldPanel("body"),
    ]

    parent_page_types = ["home.HomePage"]
    subpage_types = []

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        if self.tipo == "autoridades":
            context["autoridades"] = Autoridad.objects.all()
        return context


# ---------- Fase 3: Iglesias ----------
class IglesiasIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    parent_page_types = ["home.HomePage"]
    subpage_types = ["home.IglesiaPage"]

    def live_children(self):
        return self.get_children().live()

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        children = list(self.live_children().specific())
        by_provincia = {}
        for iglesia in children:
            prov = (iglesia.provincia or "").strip() or "Sin provincia"
            by_provincia.setdefault(prov, []).append(iglesia)
        # Ordenar provincias por nombre; dentro de cada una, iglesias por título
        for prov in by_provincia:
            by_provincia[prov].sort(key=lambda p: (p.title or "").lower())
        context["iglesias_por_provincia"] = sorted(by_provincia.items(), key=lambda x: x[0].lower())
        return context


class IglesiaPage(Page):
    """Ficha de una iglesia; puede sincronizarse desde la API de la intranet (intranet_id)."""
    intranet_id = models.IntegerField(
        null=True,
        blank=True,
        unique=True,
        help_text="ID en la intranet; usado al sincronizar con la API para actualizar esta ficha.",
    )
    nombre = models.CharField(max_length=255, blank=True)
    direccion = models.CharField(max_length=500, blank=True)
    ciudad = models.CharField(max_length=100, blank=True)
    provincia = models.CharField(max_length=100, blank=True)
    horarios = RichTextField(blank=True)
    pastor_nombre = models.CharField(max_length=255, blank=True)
    pastor_email = models.EmailField(blank=True)
    pastor_telefono = models.CharField(max_length=50, blank=True)
    mostrar_contacto_publicamente = models.BooleanField(default=False)
    redes = StreamField([
        ("enlace", LINK_BLOCK),
    ], blank=True, use_json_field=True)
    mapa_url = models.URLField(blank=True, help_text="Link a Google Maps o mapa")
    latitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitud = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    content_panels = Page.content_panels + [
        MultiFieldPanel([
            FieldPanel("intranet_id"),
            FieldPanel("nombre"),
            FieldPanel("direccion"),
            FieldPanel("ciudad"),
            FieldPanel("provincia"),
            FieldPanel("horarios"),
        ], heading="Ubicación y horarios"),
        MultiFieldPanel([
            FieldPanel("pastor_nombre"),
            FieldPanel("pastor_email"),
            FieldPanel("pastor_telefono"),
            FieldPanel("mostrar_contacto_publicamente"),
        ], heading="Pastor / contacto"),
        FieldPanel("redes"),
        MultiFieldPanel([
            FieldPanel("mapa_url"),
            FieldPanel("latitud"),
            FieldPanel("longitud"),
        ], heading="Ubicación en mapa"),
    ]

    parent_page_types = ["home.IglesiasIndexPage"]
    subpage_types = []


class ChurchSiteContent(models.Model):
    """
    Contenido de la "página propia" de una iglesia (/iglesias/<slug>/sitio/).
    Editable por secretaría (todas), administrador (todas) o pastor (solo su iglesia).
    """
    iglesia_page = models.OneToOneField(
        IglesiaPage,
        on_delete=models.CASCADE,
        related_name="site_content",
        null=False,
        blank=False,
    )
    body = RichTextField(blank=True, help_text="Contenido de la página sitio de la iglesia (HTML).")
    updated_at = models.DateTimeField(auto_now=True)
    # updated_by se puede añadir después si se guarda usuario intranet

    class Meta:
        verbose_name = "Contenido sitio iglesia"
        verbose_name_plural = "Contenidos sitio iglesias"


# ---------- Fase 4: Noticias ----------
class NoticiasIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    parent_page_types = ["home.HomePage"]
    subpage_types = ["home.NoticiaPage"]

    def get_noticias(self):
        return NoticiaPage.objects.child_of(self).live().order_by("-date")


class NoticiaPage(Page):
    date = models.DateField("Fecha")
    autor = models.CharField(max_length=255, blank=True)
    intro = RichTextField(blank=True)
    body = RichTextField(blank=True)
    imagen_destacada = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    content_panels = Page.content_panels + [
        FieldPanel("date"),
        FieldPanel("autor"),
        FieldPanel("intro"),
        FieldPanel("body"),
        FieldPanel("imagen_destacada"),
    ]

    parent_page_types = ["home.NoticiasIndexPage"]
    subpage_types = []


# ---------- Fase 5: Recursos ----------
class RecursosIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    parent_page_types = ["home.HomePage"]
    subpage_types = ["home.RecursoPage"]

    def live_children(self):
        return self.get_children().live()


class RecursoPage(Page):
    TIPO_CHOICES = [
        ("documento", "Documento (PDF, etc.)"),
        ("imagen", "Imagen"),
    ]
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default="documento")
    descripcion = RichTextField(blank=True)
    documento = models.ForeignKey(
        "wagtaildocs.Document",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    imagen = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    content_panels = Page.content_panels + [
        FieldPanel("tipo"),
        FieldPanel("descripcion"),
        FieldPanel("documento"),
        FieldPanel("imagen"),
    ]

    parent_page_types = ["home.RecursosIndexPage"]
    subpage_types = []


# ---------- Fase 6: Radios ----------
class RadiosIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

    parent_page_types = ["home.HomePage"]
    subpage_types = ["home.RadioPage"]

    def live_children(self):
        return self.get_children().live()

    def get_context(self, request, *args, **kwargs):
        import logging
        context = super().get_context(request, *args, **kwargs)
        try:
            from home.stream_radios import obtener_radios_stream
            context["stream_radios"] = obtener_radios_stream(timeout=8)
        except Exception as e:
            logging.getLogger(__name__).warning(
                "No se pudo obtener radios de imparg.org/stream/: %s", e
            )
            context["stream_radios"] = []
        return context


class RadioPage(Page):
    stream_url = models.URLField("URL del stream", blank=True)
    programacion = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("stream_url"),
        FieldPanel("programacion"),
    ]

    parent_page_types = ["home.RadiosIndexPage"]
    subpage_types = []


# ---------- Fase 7: Contacto (formulario) ----------
class ContactoPage(AbstractEmailForm):
    intro = RichTextField(blank=True)
    texto_gracias = RichTextField(blank=True, help_text="Mensaje al enviar el formulario")

    content_panels = AbstractEmailForm.content_panels + [
        FieldPanel("intro"),
        InlinePanel("form_fields", label="Campos del formulario"),
        FieldPanel("texto_gracias"),
    ]

    parent_page_types = ["home.HomePage"]
    subpage_types = []


class FormField(AbstractFormField):
    page = models.ForeignKey(ContactoPage, on_delete=models.CASCADE, related_name="form_fields")


# ---------- Fase 7: Mapa (embebible o Leaflet con iglesias) ----------
class MapaPage(Page):
    iframe_url = models.URLField(
        "URL del iframe del mapa",
        blank=True,
        help_text="URL de la app del mapa (ej. imparg.org/.../mapa). Si está vacío, se muestra el mapa de iglesias con Leaflet.",
    )
    embed_code = models.TextField(
        "Código de embed (alternativa)",
        blank=True,
        help_text="Si no usás URL, pegá el código iframe aquí.",
    )

    content_panels = Page.content_panels + [
        FieldPanel("iframe_url"),
        FieldPanel("embed_code"),
    ]

    parent_page_types = ["home.HomePage"]
    subpage_types = []

    def get_context(self, request, *args, **kwargs):
        context = super().get_context(request, *args, **kwargs)
        if not self.iframe_url and not self.embed_code:
            iglesias = []
            for iglesia in IglesiaPage.objects.live().filter(
                latitud__isnull=False, longitud__isnull=False
            ):
                iglesias.append({
                    "title": iglesia.title,
                    "lat": float(iglesia.latitud),
                    "lng": float(iglesia.longitud),
                    "direccion": iglesia.direccion or "",
                    "ciudad": iglesia.ciudad or "",
                    "pastor_nombre": iglesia.pastor_nombre or "",
                    "url": iglesia.get_url(request=request),
                })
            context["iglesias"] = iglesias
        else:
            context["iglesias"] = []
        return context


# ---------- Autoridades (Obispos) - Snippet para la página Autoridades ----------
class Autoridad(models.Model):
    """Obispo o autoridad de la IMPA. Orden 0 = actual (arriba); mayor = anteriores."""
    nombre = models.CharField(max_length=200)
    periodo = models.CharField(max_length=100, blank=True, help_text="Ej: 2025-actualidad, 2004-2025, 1995-2003")
    foto = models.ForeignKey(
        "wagtailimages.Image",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )
    descripcion = RichTextField(blank=True, help_text="Breve reseña o cargo.")
    orden = models.PositiveSmallIntegerField(
        default=0,
        help_text="0 = obispo actual (se muestra primero). Mayores = anteriores.",
    )

    panels = [
        FieldPanel("nombre"),
        FieldPanel("periodo"),
        FieldPanel("foto"),
        FieldPanel("descripcion"),
        FieldPanel("orden"),
    ]

    class Meta:
        ordering = ["orden"]
        verbose_name = "Autoridad (Obispo)"
        verbose_name_plural = "Autoridades (Obispos)"

    def __str__(self):
        return f"{self.nombre} ({self.periodo or 'sin período'})"


register_snippet(Autoridad)
