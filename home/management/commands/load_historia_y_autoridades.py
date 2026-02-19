"""
Carga en el sitio la línea de tiempo (Historia) y las autoridades (obispos)
extraídas del respaldo bkp-site.

Ejecutar una vez:

  python manage.py load_historia_y_autoridades

- Busca la página Historia (slug=historia) y le llena el body con la línea de tiempo.
- Crea los registros de Autoridad (obispos) con espacio para fotos; el actual (orden=0) primero.

No borra datos existentes de autoridades: si ya hay registros, los omite o actualiza
según --update (por defecto no actualiza, solo crea los que falten).
"""
from django.core.management.base import BaseCommand
from wagtail.models import Page

from home.models import HomePage, InstitutionalPage, Autoridad


# Línea de tiempo: lista de (tipo_block, valor) para StreamField body de Historia
TIMELINE_BLOCKS = [
    ("heading", "Nuestra Historia – Línea de Tiempo"),
    (
        "paragraph",
        "<p>Misma raíz, casa propia. Compartimos la fe y doctrina con la IMPCH (Chile), "
        "y en Argentina hemos crecido con identidad y organización independiente.</p>",
    ),
    ("heading", "1909 – Raíz en Chile – Nace la IMPCH"),
    (
        "paragraph",
        "<p>Avivamiento metodista pentecostal en Chile. Fundación de la Iglesia Metodista "
        "Pentecostal de Chile (IMPCH): nuestra raíz doctrinal y espiritual.</p>",
    ),
    ("heading", "1960 – Inicio en Argentina – Envío misionero"),
    (
        "paragraph",
        "<p>Obispo Manuel Umaña Salinas → Luis Álvarez Gutiérrez. El hermano Luis Álvarez "
        "se radica en Buenos Aires para iniciar la obra metodista pentecostal en la "
        "República Argentina.</p>",
    ),
    ("heading", "Década del 60 – Expansión al Sur Argentino"),
    (
        "paragraph",
        "<p>Pastor Marcelino Vera Cárcamo. Desde el sur de Chile se extiende la obra hacia "
        "la Patagonia argentina, consolidando nuevas congregaciones.</p>",
    ),
    ("heading", "1995 – Sucesión episcopal"),
    (
        "paragraph",
        "<p>Rev. Claudio Vera Navarrete, San Carlos de Bariloche. Tras el fallecimiento del "
        "Obispo Luis Álvarez Gutiérrez, es elegido Obispo Presidente el Rev. Claudio Vera "
        "Navarrete (1995–2003).</p>",
    ),
    ("heading", "2004 – Obispo Germán Ojeda Arteaga"),
    (
        "paragraph",
        "<p>Ciudad de Neuquén – Barrio Confluencia. Continuidad de la organización nacional "
        "y fortalecimiento institucional en todo el territorio argentino.</p>",
    ),
    ("heading", "2025 – Obispo Gustavo Mardones Zapata"),
    (
        "paragraph",
        "<p>Las Heras, Provincia de Santa Cruz. Elegido en abril de 2025 como Obispo "
        "Presidente de la IMPA.</p>",
    ),
    ("heading", "Hoy"),
    (
        "paragraph",
        "<p>+100 pastores, ~120 iglesias. Identidad nacional y reconocimiento legal: "
        "Fichero Nacional de Culto Nº 397 – Personería Jurídica 0509. Misión: predicar "
        "a Cristo, discipular y servir a la Nación.</p>",
    ),
    (
        "paragraph",
        "<p><strong>Nota:</strong> Esta cronología se elabora con memoria institucional y "
        "documentación en proceso de digitalización. Las fechas y actos formales podrán "
        "ampliarse con actas, resoluciones y registros históricos.</p>",
    ),
]

# Obispos: (nombre, periodo, descripcion, orden). orden=0 = actual (arriba).
AUTORIDADES_DATA = [
    (
        "Gustavo Mardones Zapata",
        "2025 – actualidad",
        "Obispo Presidente de la IMPA. Las Heras, Provincia de Santa Cruz. Elegido en abril de 2025.",
        0,
    ),
    (
        "Germán Ojeda Arteaga",
        "2004 – 2025",
        "Obispo Presidente. Ciudad de Neuquén – Barrio Confluencia. Continuidad de la organización nacional y fortalecimiento institucional.",
        1,
    ),
    (
        "Claudio Vera Navarrete",
        "1995 – 2003",
        "Obispo Presidente. Rev. Claudio Vera Navarrete, San Carlos de Bariloche. Elegido tras el fallecimiento del Obispo Luis Álvarez Gutiérrez.",
        2,
    ),
    (
        "Luis Álvarez Gutiérrez",
        "1960 – 1995",
        "Inició la obra metodista pentecostal en la República Argentina. Enviado por el Obispo Manuel Umaña Salinas (IMPCH), se radicó en Buenos Aires.",
        3,
    ),
]


class Command(BaseCommand):
    help = "Carga la línea de tiempo en Historia y las autoridades (obispos) en el sitio."

    def add_arguments(self, parser):
        parser.add_argument(
            "--update",
            action="store_true",
            help="Actualizar texto de la página Historia y descripciones de autoridades si ya existen.",
        )

    def handle(self, *args, **options):
        update = options["update"]
        root = Page.objects.type(HomePage).filter(depth=2).first()
        if not root:
            self.stderr.write(
                self.style.ERROR("No se encontró HomePage raíz. Ejecutá create_institutional_pages antes.")
            )
            return

        root = root.specific

        # ----- Historia: página con slug historia -----
        historia = (
            root.get_children()
            .filter(slug="historia")
            .type(InstitutionalPage)
            .first()
        )
        if historia:
            historia = historia.specific
            field = InstitutionalPage._meta.get_field("body")
            stream_block = field.stream_block
            new_body = stream_block.to_python(TIMELINE_BLOCKS)
            historia.body = new_body
            historia.save()
            self.stdout.write(self.style.SUCCESS("  Historia: línea de tiempo cargada en /historia/"))
        else:
            self.stdout.write(
                self.style.WARNING("  No existe la página Historia. Ejecutá: python manage.py create_institutional_pages")
            )

        # ----- Autoridades: snippet Autoridad -----
        created = 0
        updated = 0
        for nombre, periodo, descripcion, orden in AUTORIDADES_DATA:
            aut, is_new = Autoridad.objects.get_or_create(
                nombre=nombre,
                defaults={"periodo": periodo, "descripcion": descripcion, "orden": orden},
            )
            if is_new:
                created += 1
                self.stdout.write(self.style.SUCCESS(f"  Creada autoridad: {nombre}"))
            elif update:
                aut.periodo = periodo
                aut.descripcion = descripcion
                aut.orden = orden
                aut.save()
                updated += 1
                self.stdout.write(self.style.SUCCESS(f"  Actualizada autoridad: {nombre}"))

        if created or updated:
            self.stdout.write(
                self.style.SUCCESS(f"\nListo. Autoridades: {created} creadas, {updated} actualizadas.")
            )
        elif not update:
            self.stdout.write(
                self.style.SUCCESS("\nListo. Las autoridades ya existían (usá --update para actualizar).")
            )
