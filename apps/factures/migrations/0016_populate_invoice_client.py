# Populate Invoice.client from Invoice.quote.client for existing records

from django.db import migrations


def forwards(apps, schema_editor):
    Invoice = apps.get_model("factures", "Invoice")
    updated = Invoice.objects.filter(
        client__isnull=True,
        quote__isnull=False,
    ).exclude(quote__client__isnull=True)
    for inv in updated:
        inv.client = inv.quote.client
        inv.save(update_fields=["client"])


def backwards(apps, schema_editor):
    pass  # No need to reverse: client FK is nullable


class Migration(migrations.Migration):

    dependencies = [
        ("factures", "0015_invoice_client"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
