# Generated manually for trusted logos admin management.

from django.db import migrations, models


def seed_trusted_logos(apps, schema_editor):
    TrustedLogo = apps.get_model("pages", "TrustedLogo")
    TrustedLogo.objects.get_or_create(
        name="Nettoyage Express",
        defaults={
            "legacy_static_path": "img/trusted/nettoyage-express-logo.png",
            "order": 10,
            "is_active": True,
        },
    )
    TrustedLogo.objects.get_or_create(
        name="EEBC",
        defaults={
            "legacy_static_path": "img/trusted/eebc-logo.png",
            "order": 20,
            "is_active": True,
        },
    )


def remove_seeded_trusted_logos(apps, schema_editor):
    TrustedLogo = apps.get_model("pages", "TrustedLogo")
    TrustedLogo.objects.filter(
        name__in=["Nettoyage Express", "EEBC"],
        logo__isnull=True,
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("pages", "0004_alter_testimonial_options_testimonial_avatar_url_and_more"),
    ]

    operations = [
        migrations.CreateModel(
            name="TrustedLogo",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=200, verbose_name="Nom")),
                ("logo", models.ImageField(blank=True, null=True, help_text="PNG, WebP ou JPG recommandé avec fond transparent.", upload_to="trusted_logos/", verbose_name="Logo")),
                ("legacy_static_path", models.CharField(blank=True, default="", editable=False, help_text="Chemin statique conservé pour les logos historiques.", max_length=255)),
                ("is_active", models.BooleanField(default=True, verbose_name="Actif")),
                ("order", models.PositiveIntegerField(default=0, verbose_name="Ordre d'affichage")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Logo de confiance",
                "verbose_name_plural": "Logos — Ils nous font confiance",
                "ordering": ["order", "name"],
            },
        ),
        migrations.RunPython(seed_trusted_logos, remove_seeded_trusted_logos),
    ]
