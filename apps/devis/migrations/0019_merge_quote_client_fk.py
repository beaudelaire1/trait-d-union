"""Rewire Quote.client FK from devis.Client to clients.ClientProfile.

Strategy (safe for both SQLite and PostgreSQL):
1. Add a temp column `_new_client_id`
2. Data migration: populate from old client → linked_profile mapping
3. Remove old `client` FK (drops old column)
4. Add new `client` FK to ClientProfile (nullable initially)
5. Copy _new_client_id → client_id
6. Remove temp column
7. Make client NOT NULL
8. Delete the old devis.Client model
"""
import django.db.models.deletion
from django.db import migrations, models


def map_quote_clients(apps, schema_editor):
    """Populate temp column with mapped ClientProfile IDs."""
    db = schema_editor.connection.alias
    Quote = apps.get_model('devis', 'Quote')
    Client = apps.get_model('devis', 'Client')

    # Build mapping: old devis.Client.pk → ClientProfile.pk
    mapping = {}
    for c in Client.objects.using(db).all():
        if c.linked_profile_id:
            mapping[c.pk] = c.linked_profile_id

    for quote in Quote.objects.using(db).all():
        old_id = quote.client_id
        if old_id and old_id in mapping:
            quote._new_client_id = mapping[old_id]
            quote.save(using=db, update_fields=['_new_client_id'])


def copy_temp_to_client(apps, schema_editor):
    """Copy _new_client_id into the new client_id column."""
    db = schema_editor.connection.alias
    Quote = apps.get_model('devis', 'Quote')
    for quote in Quote.objects.using(db).filter(_new_client_id__isnull=False):
        quote.client_id = quote._new_client_id
        quote.save(using=db, update_fields=['client_id'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ('devis', '0018_remove_client_idx_client_linked_profile_and_more'),
        ('clients', '0011_populate_from_devis_client'),
        # factures migration must run BEFORE we delete Client model
        ('factures', '0018_merge_invoice_client_fk'),
    ]

    operations = [
        # 1. Add temp column
        migrations.AddField(
            model_name='quote',
            name='_new_client_id',
            field=models.IntegerField(null=True, blank=True),
        ),
        # 2. Populate temp column from old FK → linked_profile mapping
        migrations.RunPython(map_quote_clients, noop),
        # 3. Remove old client FK (devis.Client)
        migrations.RemoveField(
            model_name='quote',
            name='client',
        ),
        # 4. Add new client FK (clients.ClientProfile), nullable initially
        migrations.AddField(
            model_name='quote',
            name='client',
            field=models.ForeignKey(
                null=True, blank=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name='quotes',
                to='clients.clientprofile',
                verbose_name='Client',
            ),
        ),
        # 5. Copy temp → new client_id
        migrations.RunPython(copy_temp_to_client, noop),
        # 6. Remove temp column
        migrations.RemoveField(
            model_name='quote',
            name='_new_client_id',
        ),
        # 7. Make client NOT NULL
        migrations.AlterField(
            model_name='quote',
            name='client',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name='quotes',
                to='clients.clientprofile',
                verbose_name='Client',
            ),
        ),
        # 8. Remove old indexes on Client model
        migrations.RemoveIndex(
            model_name='client',
            name='idx_devis_client_email',
        ),
        # 9. Delete the old Client model
        migrations.DeleteModel(
            name='Client',
        ),
    ]
