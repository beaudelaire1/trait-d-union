# Step 2/3: Copy existing option field values into service_options JSON

from django.db import migrations


def forwards(apps, schema_editor):
    Quote = apps.get_model("devis", "Quote")
    for q in Quote.objects.all():
        opts = {}
        if q.included_support_months:
            opts["included_support_months"] = q.included_support_months
        if q.installment_plan:
            opts["installment_plan"] = True
        if q.money_back_guarantee:
            opts["money_back_guarantee"] = True
        if q.unlimited_revisions:
            opts["unlimited_revisions"] = True
        if opts:
            q.service_options = opts
            q.save(update_fields=["service_options"])


def backwards(apps, schema_editor):
    Quote = apps.get_model("devis", "Quote")
    for q in Quote.objects.all():
        opts = q.service_options or {}
        q.included_support_months = opts.get("included_support_months", 0)
        q.installment_plan = opts.get("installment_plan", False)
        q.money_back_guarantee = opts.get("money_back_guarantee", False)
        q.unlimited_revisions = opts.get("unlimited_revisions", False)
        q.save(update_fields=[
            "included_support_months",
            "installment_plan",
            "money_back_guarantee",
            "unlimited_revisions",
        ])


class Migration(migrations.Migration):

    dependencies = [
        ("devis", "0012_remove_quote_included_support_months_and_more"),
    ]

    operations = [
        migrations.RunPython(forwards, backwards),
    ]
