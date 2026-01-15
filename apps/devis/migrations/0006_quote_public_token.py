from django.db import migrations, models


def populate_public_token(apps, schema_editor):
    import secrets
    Quote = apps.get_model("devis", "Quote")
    for q in Quote.objects.all():
        if not getattr(q, "public_token", ""):
            q.public_token = secrets.token_urlsafe(32)
            q.save(update_fields=["public_token"])


class Migration(migrations.Migration):

    dependencies = [
        ("devis", "0005_quotevalidation"),
    ]

    operations = [
        migrations.AddField(
            model_name="quote",
            name="public_token",
            field=models.CharField(blank=True, help_text="Jeton public stable pour consulter le PDF du devis.", max_length=64, unique=True),
        ),
        migrations.RunPython(populate_public_token, migrations.RunPython.noop),
    ]
