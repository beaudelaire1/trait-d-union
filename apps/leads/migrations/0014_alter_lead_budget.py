from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("leads", "0013_add_newsletter_campaign"),
    ]

    operations = [
        migrations.AlterField(
            model_name="lead",
            name="budget",
            field=models.CharField(
                blank=True,
                choices=[
                    ("small", "< 2 000 €"),
                    ("medium", "2 000 € – 5 000 €"),
                    ("large", "5 000 € – 8 500 €"),
                    ("enterprise", "> 8 500 € (plateforme métier)"),
                    ("discuss", "À discuter"),
                ],
                max_length=20,
                verbose_name="Budget estimé",
            ),
        ),
    ]
