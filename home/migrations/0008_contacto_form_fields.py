# Añade campos por defecto al formulario de contacto (nombre, apellido, correo, mensaje), todos opcionales.

from django.db import migrations


CONTACTO_FORM_FIELDS = [
    ("Nombre", "singleline"),
    ("Apellido", "singleline"),
    ("Correo electrónico", "email"),
    ("Mensaje", "multiline"),
]


def add_contacto_form_fields(apps, schema_editor):
    ContactoPage = apps.get_model("home", "ContactoPage")
    FormField = apps.get_model("home", "FormField")
    # Usar solo IDs para no instanciar ContactoPage (evita __init__ de Wagtail que usa .template)
    contacto_page_ids = list(ContactoPage.objects.values_list("pk", flat=True))
    pages_with_fields = set(
        FormField.objects.filter(page_id__in=contacto_page_ids).values_list(
            "page_id", flat=True
        )
    )
    for page_id in contacto_page_ids:
        if page_id in pages_with_fields:
            continue
        for i, (label, field_type) in enumerate(CONTACTO_FORM_FIELDS):
            FormField.objects.create(
                page_id=page_id,
                label=label,
                field_type=field_type,
                required=False,
                sort_order=i,
            )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0007_add_church_site_content"),
    ]

    operations = [
        migrations.RunPython(add_contacto_form_fields, noop),
    ]
