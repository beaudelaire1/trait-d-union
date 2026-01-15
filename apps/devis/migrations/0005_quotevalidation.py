from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('devis', '0004_quoterequest_quoterequestphoto_alter_quote_status_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='QuoteValidation',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('token', models.CharField(max_length=64, unique=True)),
                ('code', models.CharField(max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField()),
                ('confirmed_at', models.DateTimeField(blank=True, null=True)),
                ('attempts', models.PositiveIntegerField(default=0)),
                ('quote', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='validations', to='devis.quote')),
            ],
            options={
                'verbose_name': 'validation devis',
                'verbose_name_plural': 'validations devis',
                'ordering': ['-created_at'],
            },
        ),
    ]
