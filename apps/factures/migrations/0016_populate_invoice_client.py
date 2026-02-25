# Populate Invoice.client from Invoice.quote.client for existing records

from django.db import migrations


def forwards(apps, schema_editor):
    """Bulk-update Invoice.client_id depuis Quote.client_id (SQL unique)."""
    Invoice = apps.get_model("factures", "Invoice")
    Quote = apps.get_model("devis", "Quote")

    # Sous-requête : pour chaque facture sans client, copier le client_id du devis
    Invoice.objects.filter(
        client__isnull=True,
        quote__isnull=False,
        quote__client__isnull=False,
    ).update(
        client_id=models.Subquery(
            Quote.objects.filter(pk=models.OuterRef('quote_id')).values('client_id')[:1]
        )
    )


def backwards(apps, schema_editor):
    pass  # No need to reverse: client FK is nullable


# Import nécessaire pour Subquery/OuterRef
from django.db import models


class Migration(migrations.Migration):

    dependencies = [
        ("factures", "0015_invoice_client"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
