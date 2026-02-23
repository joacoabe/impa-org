"""
Carga en la página Doctrina los Artículos de Fe de la IMPA.

Ejecutar una vez (o con --update para reemplazar el contenido):

  python manage.py load_doctrina_articulos

Requisito: debe existir la página Doctrina (slug=doctrina).
Crear con: python manage.py create_institutional_pages
"""
from django.core.management.base import BaseCommand
from wagtail.models import Page

from home.models import HomePage, InstitutionalPage


# (tipo_block, valor) para StreamField body. heading = título; paragraph = HTML.
# Sin encabezado inicial: empieza por el Artículo UNO.
DOCTRINA_BLOCKS = [
    ("heading", "UNO"),
    (
        "paragraph",
        "<p>Cree en un solo Dios (Dt 6:4; Jud 25), Trino (Mt 3:16,17; Jn 28:19; 1Jn 5:7; 2Co 13:14) "
        "y Verdadero (Jn 17:3), al cual adora en espíritu y en verdad.</p>",
    ),
    (
        "paragraph",
        "<p><strong>En sí mismo Dios es:</strong><br/>"
        "Espíritu (Jn 4:23-24)<br/>Eterno (Sal 90:2; Ex 15:18; Dt 33:27; Jer 10:10)<br/>"
        "Infinito (Sal 145:3; Ro 11:33)<br/>Inmenso (1°R 8:27; 2Cr 2:5-6)<br/>"
        "Inmutable (Mal 3:6; Nm 23:19; 1S 15:29; Stg 1:17)</p>",
    ),
    (
        "paragraph",
        "<p><strong>En relación con el Universo Dios es:</strong><br/>"
        "Creador (Gn 1:1; Is 42:5; Hch 17:24; Ap 4:11; 10:6)<br/>"
        "Conservador Providente (Sal 104:1-35; Hch 17:28; He 1:3)<br/>"
        "Omnipotente (Lc 1:37; Gn 18:14; Jer 32:17)<br/>"
        "Omnipresente (Sal 139:7-12; Jer 23:23-24; Mt 18:20)<br/>"
        "Omnisciente (Job 42:2-6; Sal 139:1-6)<br/>"
        "Sabio (Sal 104:24; Pr 3:19; Jer 10:12; Ro 11:33; Ef 3:10)<br/>"
        "Soberano (Sal 74:12; Dn 4:35; Is 33:22; Ro 9:21-22)</p>",
    ),
    (
        "paragraph",
        "<p><strong>En relación con los seres morales (seres humanos y ángeles) Dios es:</strong><br/>"
        "Amor (1Jn 3:1; 4:7-10; Jn 3:16; Ro 5:5)<br/>"
        "Santo (Ex 15:11; Lv 11:44-45; 1P 1:15-16)<br/>"
        "Justo (Gn 18:25; Ex 9:27; Dt 4:8; Sal 89:14; Ap 15:3; 16:5; 19:2)<br/>"
        "Fiel (Dt 4:31; 7:9; Jos 21:43-45; 23:14; 1S 15:29; 1Co 1:9; 1Ts 5:24)<br/>"
        "Paciente (1P 3:20; 2P 3:3,15; Ro 2:4; 9:22; Ex 34:6; Sal 86:15)<br/>"
        "Bondadoso (Sal 25:8; 145:9,15-16; Mt 5:45; Lc 6:35; Hch 14:17)<br/>"
        "Misericordioso (Sal 103:8-13; Lc 1:78; Ef 2:4-7; Tit 3:5)<br/>"
        "Veraz (Nm 23:19; Jn 14:6; 1Jn 1:5; 5:20)</p>",
    ),
    (
        "paragraph",
        "<p><strong>Trinidad:</strong> En la unidad de la Deidad hay tres Personas Divinas: "
        "Dios Padre, Dios Hijo y Dios Espíritu Santo.</p>",
    ),
    (
        "paragraph",
        "<p><strong>— Trinidad Inmanente u Ontológica:</strong><br/>"
        "El Padre es primero; el Hijo es segundo; el Espíritu Santo es tercero. "
        "El Padre, desde la eternidad, engendra al Hijo; el Espíritu Santo procede del Padre y del Hijo.</p>",
    ),
    (
        "paragraph",
        "<p><strong>— Trinidad Económica:</strong><br/>"
        "Orden de funciones (no subordinación de personas): el Padre crea, el Hijo redime y el Espíritu Santo santifica.</p>",
    ),
    ("heading", "DOS"),
    (
        "paragraph",
        "<p>Cree en Jesucristo, Único Salvador de la humanidad, Hijo Unigénito de Dios, segunda persona de la Santa Trinidad, "
        "consubstancial o de la misma substancia del Padre y engendrado de Él antes de todos los siglos, no hecho; "
        "por quien todas las cosas fueron creadas.</p>",
    ),
    (
        "paragraph",
        "<p>Por su Encarnación, sin dejar de ser Dios, se hizo hombre mediante Nacimiento Virginal, siendo concebido por obra "
        "del Espíritu Santo en el seno de la Virgen María, para asumir la naturaleza humana, redimirla y glorificarla.</p>",
    ),
    (
        "paragraph",
        "<p>Las dos naturalezas, divina y humana, conservando íntegramente sus propiedades, se juntaron en la Persona de Jesucristo, "
        "verdadero Dios y verdadero hombre, perfecto en su divinidad y en su humanidad.</p>",
    ),
    (
        "paragraph",
        "<p>Nos reconcilió con el Padre por su sacrificio vivo y expiatorio: fue crucificado, muerto y sepultado por nuestra salvación; "
        "expiando nuestras culpas y las heredadas del pecado original.</p>",
    ),
    (
        "paragraph",
        "<p>Resucitó al tercer día con cuerpo glorificado; ascendió al Cielo; entró en el Santuario Celestial; se sentó a la diestra del Padre; "
        "y es el único Mediador entre Dios y los hombres.</p>",
    ),
    ("heading", "TRES"),
    (
        "paragraph",
        "<p>Cree en la Autoridad de la Biblia, infalible Palabra de Dios, constituida por los sesenta y seis Libros Canónicos "
        "del Antiguo y del Nuevo Testamento.</p>",
    ),
    (
        "paragraph",
        "<p>Cree en la entera confiabilidad de las Santas Escrituras y en la Inspiración viva, vernal y plenaria de ellas. "
        "Las Escrituras se bastan a sí mismas: son su mejor y propio intérprete, libres de error, y tienen como centro a Jesucristo (He 1:1-2) "
        "y el Plan de Salvación.</p>",
    ),
    (
        "paragraph",
        "<p>Por esta razón, la Biblia constituye la autoridad máxima en asuntos de fe y la norma de conducta para todo cristiano que quiere hacer "
        "la voluntad de Dios. Esto fundamenta el denominado \"Libre examen de las Escrituras\": a ningún creyente debe exigírsele aceptar como "
        "artículo de fe, ni como requisito de salvación, nada que no pueda leerse en las Santas Escrituras ni por ellas probarse.</p>",
    ),
    (
        "paragraph",
        "<p>Se sugiere el uso de la Biblia Reina-Valera revisión 1960 para lograr mayor uniformidad y compresión.</p>",
    ),
    ("heading", "CUATRO"),
    (
        "paragraph",
        "<p>Acepta como Sacramento u Ordenanza de la Iglesia el Bautismo Cristiano y la Santa Cena, instituidos por Cristo, "
        "signos de la Profesión de Fe y Medio de Gracia mediante los cuales Dios obra avivando, fortaleciendo y confirmando la fe.</p>",
    ),
    (
        "paragraph",
        "<p><strong>Bautismo Cristiano:</strong><br/>"
        "Es signo de la Regeneración o Nuevo Nacimiento (Jn 3:5). Representa el ingreso a la Iglesia Visible y simboliza muerte al pecado "
        "y resurrección a una Vida Nueva (Ro 6:3-6; Col 2:12).</p>",
    ),
    (
        "paragraph",
        "<p>Sella la unión y compromiso con Jesucristo (Hch 8:36-37; 10:47-48) y es obediencia a su mandato (Mr 16:16; Mt 28:19).</p>",
    ),
    (
        "paragraph",
        "<p><strong>Modo:</strong> Aspersión (Ez 36:25), simbolizando limpieza espiritual. Se administra en el nombre de la Santa Trinidad, una sola vez: "
        "a adultos como testimonio público; y a niños o párvulos para consagración (\"Dejad a los niños…\" Mr 10:14).</p>",
    ),
    (
        "paragraph",
        "<p><strong>Fundamento del bautismo de niños:</strong> el bautismo del Nuevo Testamento reemplaza a la circuncisión del Antiguo Pacto (Gn 17:7-14; 17:12). "
        "Hay relatos que permiten afirmar práctica en la Iglesia Primitiva (Hch 2:38-39; 16:15,33; 18:8; 1Co 1:16; 10:1-2). "
        "Implica la presentación del párvulo a Dios.</p>",
    ),
    (
        "paragraph",
        "<p><strong>Santa Cena:</strong><br/>"
        "Signo conmemorativo de nuestra Redención por la muerte de Cristo y de nuestra comunión con Él. "
        "Debe administrarse conforme al mandamiento del Señor (Lc 22:19; 1Co 5:7-8).</p>",
    ),
    (
        "paragraph",
        "<p>No hay transubstanciación: la presencia de Cristo es real; pan y vino representan su cuerpo y sangre. "
        "Debe ofrecerse a todos los fieles. También anuncia proféticamente el Reino (Lc 22:18; 1Co 11:26).</p>",
    ),
    ("heading", "CINCO"),
    (
        "paragraph",
        "<p>Cree en el Bautismo con el Espíritu Santo: sello de propiedad de Dios (Ef 1:13; 4:30) y poder (Hch 1:8).</p>",
    ),
    (
        "paragraph",
        "<p>El creyente es Templo del Espíritu Santo (1Co 3:16; 6:19). Su presencia se manifiesta por el Fruto (Gá 5:22-23) y los Dones Espirituales (1Co 11—14). "
        "Por el Fruto mueren las Obras de la Carne y se conforma el carácter a Cristo; por los Dones se capacita para el servicio en la Iglesia.</p>",
    ),
    ("heading", "SEIS"),
    (
        "paragraph",
        "<p>Cree en la resurrección de los muertos y en la vida del Mundo Venidero. La plena salvación incluye resurrección y glorificación del cuerpo.</p>",
    ),
    (
        "paragraph",
        "<p>Cristo, Segundo Adán, venció la muerte: crucificado, muerto y sepultado; resucitó al tercer día con cuerpo glorificado.</p>",
    ),
    (
        "paragraph",
        "<p>Habrá dos resurrecciones (Dn 12:2; Jn 5:28-29; Hch 24:15) y juicios:</p>",
    ),
    (
        "paragraph",
        "<p><strong>a) Primera Resurrección (Ap 20:6):</strong> Resurrección de Vida antes de la Gran Tribulación; "
        "seguida por Tribunal de Cristo (Ro 14:10; 2Co 5:10), juicio de recompensa.</p>",
    ),
    (
        "paragraph",
        "<p><strong>b) Segunda Resurrección (Ap 20:5):</strong> de impíos; seguida por Juicio del Gran Trono Blanco (Ap 20:12-15), "
        "condenación y \"muerte segunda\".</p>",
    ),
    ("heading", "SIETE"),
    (
        "paragraph",
        "<p>Cree en la Parousia o Segunda Venida de Cristo en Gloria y Majestad: inminente, impredecible, personal, visible (Ap 1:7), "
        "gloriosa y triunfante (1Co 15:25; Ap 19:11-16), y premilenial.</p>",
    ),
    (
        "paragraph",
        "<p>Ocurre en dos etapas: (1) antes del Anticristo y la Gran Tribulación: Primera Resurrección y Arrebatamiento (1Ts 4:16-17; Mr 13:26-27); "
        "(2) al final de la Gran Tribulación: Cristo viene con sus santos, destruye al Anticristo y establece su Reino Mesiánico o Milenial.</p>",
    ),
    ("heading", "OCHO"),
    (
        "paragraph",
        "<p>Cree en la Justificación por la sola Fe en Jesucristo y no por obras de la Ley. Es acto judicial de Dios: declara justo al creyente "
        "por la justicia de Cristo, al aceptarle por fe.</p>",
    ),
    (
        "paragraph",
        "<p>La salvación depende de la Obra Expiatoria de Cristo. Hay libre albedrío: aceptar o rechazar la gracia. "
        "Las buenas obras no salvan, son fruto de vida regenerada.</p>",
    ),
    ("heading", "NUEVE"),
    (
        "paragraph",
        "<p>Cree en la Santa Iglesia Universal, Cuerpo de Cristo, formada por cristianos de todos los tiempos y lugares que aceptaron y aceptarán "
        "a Jesucristo como Señor y Salvador.</p>",
    ),
    (
        "paragraph",
        "<p>Como Iglesia Local, la Iglesia Metodista Pentecostal Argentina es parte y expresión de la Iglesia Universal. Su finalidad es cumplir la misión "
        "de anunciar el Evangelio a todas las naciones, mediante evangelización, predicación, enseñanza, adoración, sacramentos, servicio y comunión.</p>",
    ),
    ("heading", "DIEZ"),
    (
        "paragraph",
        "<p>Cree en el Sacerdocio Universal de los Creyentes. El sacerdocio aarónico culmina con Cristo, Sumo Sacerdote según Melquisedec (He 5:10), quien intercede.</p>",
    ),
    (
        "paragraph",
        "<p>Acceso directo al Trono de la Gracia (He 4:16) por los méritos de Cristo; no se requiere mediación de sacerdotes humanos o santos (1Ti 2:5). "
        "Cada creyente es sacerdote para Dios (1P 2:9).</p>",
    ),
    ("heading", "ONCE"),
    (
        "paragraph",
        "<p>Cree en la Sanidad Divina como parte integral del Evangelio y promesa de Jesucristo (\"sobre los enfermos pondrán sus manos…\" Mr 16:17).</p>",
    ),
    (
        "paragraph",
        "<p>Cristo continúa su obra en la Tierra por su Iglesia (Jn 14:12). Por ungimiento o imposición de manos (Stg 5:14-15), Dios usa a los cristianos para sanidad.</p>",
    ),
    ("heading", "DOCE"),
    (
        "paragraph",
        "<p>Cree en la existencia del mundo espiritual: ángeles y demonios.</p>",
    ),
    (
        "paragraph",
        "<p>Los ángeles son espíritus ministradores (He 1:14). Los demonios son ángeles caídos al servicio de Satanás, causantes de males.</p>",
    ),
    (
        "paragraph",
        "<p>El creyente debe orar en todo tiempo y usar la Armadura de Dios (Ef 6:10-18), resistiendo al diablo (1P 5:8-9; Stg 4:7).</p>",
    ),
    (
        "paragraph",
        "<p>Cristo prometió autoridad para liberar a los endemoniados: \"En mi nombre echarán fuera demonios\" (Mr 16:17).</p>",
    ),
]


class Command(BaseCommand):
    help = "Carga los Artículos de Fe en la página Doctrina."

    def add_arguments(self, parser):
        parser.add_argument(
            "--update",
            action="store_true",
            help="Reemplazar el contenido actual del body de la página Doctrina.",
        )

    def handle(self, *args, **options):
        root = Page.objects.type(HomePage).filter(depth=2).first()
        if not root:
            self.stderr.write(
                self.style.ERROR("No se encontró HomePage raíz. Ejecutá create_institutional_pages antes.")
            )
            return

        root = root.specific
        doctrina = (
            root.get_children()
            .filter(slug="doctrina")
            .type(InstitutionalPage)
            .first()
        )
        if not doctrina:
            self.stderr.write(
                self.style.ERROR("No existe la página Doctrina. Ejecutá: python manage.py create_institutional_pages")
            )
            return

        doctrina = doctrina.specific
        if doctrina.body and not options["update"]:
            self.stdout.write(
                self.style.WARNING("La página Doctrina ya tiene contenido. Usá --update para reemplazarlo.")
            )
            return

        field = InstitutionalPage._meta.get_field("body")
        stream_block = field.stream_block
        doctrina.body = stream_block.to_python(DOCTRINA_BLOCKS)
        doctrina.save()
        self.stdout.write(self.style.SUCCESS("Doctrina: Artículos de Fe cargados en /doctrina/"))
