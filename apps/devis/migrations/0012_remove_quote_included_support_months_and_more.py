# Step 1/3: Add service_options JSONField (keep old fields for data migration)

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('devis', '0011_alter_quote_options_client_idx_devis_client_email_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='quote',
            name='service_options',
            field=models.JSONField(blank=True, default=dict, help_text='Options additionnelles du devis : included_support_months, installment_plan, money_back_guarantee, unlimited_revisions', verbose_name='Options de service'),
        ),
    ]
