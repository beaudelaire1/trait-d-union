from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("portfolio", "0008_project_audit_fields"),
    ]

    operations = [
        migrations.AlterField(
            model_name="project",
            name="audit_last_run_at",
            field=models.DateTimeField(
                blank=True,
                help_text="Mis à jour automatiquement à chaque audit.",
                null=True,
                verbose_name="Audit — dernière exécution",
            ),
        ),
        migrations.AlterField(
            model_name="project",
            name="audit_results",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text=(
                    "Scores agrégés par catégorie (PageSpeed, Mozilla Observatory, "
                    "SSL Labs). Alimenté par `manage.py audit_portfolio_projects`. "
                    "Vide → le template affiche les liens vers les outils externes."
                ),
                verbose_name="Audit (Ch.05)",
            ),
        ),
    ]
