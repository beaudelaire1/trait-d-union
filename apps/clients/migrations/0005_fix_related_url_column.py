# Fix missing related_url column

from django.db import migrations, models


def do_nothing(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0004_remove_clientnotification_link_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='clientnotification',
            name='related_url',
            field=models.CharField(blank=True, max_length=255, verbose_name='URL associée'),
            preserve_default=True,
        ),
    ]
