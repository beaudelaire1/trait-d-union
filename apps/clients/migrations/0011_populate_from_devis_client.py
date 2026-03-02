"""Data migration: populate ClientProfile from devis.Client records.

For each devis_client row:
- If linked_profile exists → update that ClientProfile with contact fields
- If no linked_profile → create a new ClientProfile (user=None)

Also stores old devis.Client PK → new ClientProfile PK mapping
in the devis_client.linked_profile_id column (for FK rewrite migrations).
"""
from django.db import migrations


def populate_client_profiles(apps, schema_editor):
    """Copy contact info from devis.Client into clients.ClientProfile."""
    db = schema_editor.connection.alias
    Client = apps.get_model('devis', 'Client')
    ClientProfile = apps.get_model('clients', 'ClientProfile')

    for c in Client.objects.using(db).all():
        if c.linked_profile_id:
            # Update existing profile with contact fields
            profile = ClientProfile.objects.using(db).get(pk=c.linked_profile_id)
            profile.full_name = c.full_name or profile.full_name or ''
            profile.email = c.email or profile.email or ''
            profile.phone = c.phone or profile.phone or ''
            profile.company_name = getattr(c, 'company', '') or profile.company_name or ''
            profile.address_line = getattr(c, 'address_line', '') or profile.address_line or ''
            profile.city = getattr(c, 'city', '') or profile.city or ''
            profile.zip_code = getattr(c, 'zip_code', '') or profile.zip_code or ''
            profile.save(using=db)
        else:
            # Create new ClientProfile for this contact (no portal user)
            profile = ClientProfile.objects.using(db).create(
                full_name=c.full_name or '',
                email=c.email or '',
                phone=c.phone or '',
                company_name=getattr(c, 'company', '') or '',
                address_line=getattr(c, 'address_line', '') or '',
                city=getattr(c, 'city', '') or '',
                zip_code=getattr(c, 'zip_code', '') or '',
                user=None,
            )
            # Store mapping for FK rewrite migrations
            c.linked_profile_id = profile.pk
            c.save(using=db, update_fields=['linked_profile'])


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('clients', '0010_merge_client_fields'),
        ('devis', '0018_remove_client_idx_client_linked_profile_and_more'),
    ]

    operations = [
        migrations.RunPython(populate_client_profiles, noop),
    ]
