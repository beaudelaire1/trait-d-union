"""Ajoute les champs d'audit performance / conformité pour le Ch.05."""
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("portfolio", "0007_add_performance_indexes"),
    ]

    operations = [
        migrations.AddField(
            model_name="project",
            name="audit_results",
            field=models.JSONField(
                blank=True,
                default=dict,
                help_text=(
                    "Résultats d'audit (Ch.05). Format : "
                    "{ 'performance': {'score': 95, 'measured_at': '...'}, "
                    "  'seo': {...}, 'accessibility': {...}, "
                    "  'best_practices': {...}, 'security': {...}, 'ssl': {...} }. "
                    "Alimenté par `python manage.py audit_portfolio_projects`."
                ),
                verbose_name="Audit (Ch.05)",
            ),
        ),
        migrations.AddField(
            model_name="project",
            name="audit_last_run_at",
            field=models.DateTimeField(
                blank=True,
                null=True,
                help_text="Dernière exécution de l'audit automatisé.",
                verbose_name="Audit — dernière exécution",
            ),
        ),
    ]
