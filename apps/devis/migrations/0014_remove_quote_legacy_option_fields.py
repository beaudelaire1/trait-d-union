# Step 3/3: Remove legacy option fields now that data lives in service_options

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("devis", "0013_migrate_quote_options_to_json"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="quote",
            name="included_support_months",
        ),
        migrations.RemoveField(
            model_name="quote",
            name="installment_plan",
        ),
        migrations.RemoveField(
            model_name="quote",
            name="money_back_guarantee",
        ),
        migrations.RemoveField(
            model_name="quote",
            name="unlimited_revisions",
        ),
    ]
