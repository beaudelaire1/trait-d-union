"""Rewire Invoice.client FK from devis.Client to clients.ClientProfile.

Same strategy as devis/0019:
1. Add temp column
2. Data migration via mapping
3. Remove old FK, add new FK
4. Copy data, cleanup
"""
import django.db.models.deletion
from django.db import migrations, models


def map_invoice_clients(apps, schema_editor):
    """Populate temp column with mapped ClientProfile IDs."""
    db = schema_editor.connection.alias
    Invoice = apps.get_model('factures', 'Invoice')
    Client = apps.get_model('devis', 'Client')

    # Build mapping: old devis.Client.pk → ClientProfile.pk
    mapping = {}
    for c in Client.objects.using(db).all():
        if c.linked_profile_id:
            mapping[c.pk] = c.linked_profile_id

    for inv in Invoice.objects.using(db).filter(client_id__isnull=False):
        old_id = inv.client_id
        if old_id in mapping:
            inv._new_client_id = mapping[old_id]
            inv.save(using=db, update_fields=['_new_client_id'])


def copy_temp_to_client(apps, schema_editor):
    """Copy _new_client_id into the new client_id column."""
    db = schema_editor.connection.alias
    Invoice = apps.get_model('factures', 'Invoice')
    for inv in Invoice.objects.using(db).filter(_new_client_id__isnull=False):
        inv.client_id = inv._new_client_id
        inv.save(using=db, update_fields=['client_id'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    atomic = False

    dependencies = [
        ('factures', '0017_add_performance_indexes'),
        ('clients', '0011_populate_from_devis_client'),
        # Must run BEFORE devis/0019 deletes Client model
        ('devis', '0018_remove_client_idx_client_linked_profile_and_more'),
    ]

    operations = [
        # 1. Add temp column
        migrations.AddField(
            model_name='invoice',
            name='_new_client_id',
            field=models.IntegerField(null=True, blank=True),
        ),
        # 2. Populate temp column
        migrations.RunPython(map_invoice_clients, noop),
        # 3. Remove old client FK (devis.Client)
        migrations.RemoveField(
            model_name='invoice',
            name='client',
        ),
        # 4. Add new client FK (clients.ClientProfile), nullable
        migrations.AddField(
            model_name='invoice',
            name='client',
            field=models.ForeignKey(
                null=True, blank=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='invoices',
                to='clients.clientprofile',
                verbose_name='Client',
            ),
        ),
        # 5. Copy temp → new client_id
        migrations.RunPython(copy_temp_to_client, noop),
        # 6. Remove temp column
        migrations.RemoveField(
            model_name='invoice',
            name='_new_client_id',
        ),
    ]
