# Migration manuelle : retire SiteDiagnostic de l'état audit (table renommée par diagnostic.0001).

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('audit', '0004_sitediagnostic'),
        ('diagnostic', '0001_initial'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.DeleteModel(
                    name='SiteDiagnostic',
                ),
            ],
            database_operations=[],
        ),
    ]
