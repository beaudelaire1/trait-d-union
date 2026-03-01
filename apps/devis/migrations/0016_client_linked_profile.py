"""Add linked_profile FK on Client for secure portal lookups."""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0009_add_performance_indexes'),
        ('devis', '0015_add_performance_indexes'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='linked_profile',
            field=models.ForeignKey(
                blank=True,
                help_text='Lien direct vers le compte portail client (rempli automatiquement).',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='linked_clients',
                to='clients.clientprofile',
                verbose_name='Profil portail',
            ),
        ),
        migrations.AddIndex(
            model_name='client',
            index=models.Index(fields=['linked_profile'], name='idx_client_linked_profile'),
        ),
    ]
