# Generated manually for ChurchSiteContent (página sitio de iglesia)

import django.db.models.deletion
import wagtail.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("home", "0006_add_iglesia_intranet_id"),
    ]

    operations = [
        migrations.CreateModel(
            name="ChurchSiteContent",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("body", wagtail.fields.RichTextField(blank=True, help_text="Contenido de la página sitio de la iglesia (HTML).")),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "iglesia_page",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="site_content",
                        to="home.iglesiapage",
                    ),
                ),
            ],
            options={
                "verbose_name": "Contenido sitio iglesia",
                "verbose_name_plural": "Contenidos sitio iglesias",
            },
        ),
    ]
