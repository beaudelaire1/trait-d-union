"""Backfill Client.linked_profile from existing email matches.

For each Client (devis) that has an email matching a User with a ClientProfile,
set the linked_profile FK. This replaces the fragile email-based lookup pattern.
"""
from django.db import migrations


def backfill_linked_profiles(apps, schema_editor):
    """Link existing Client records to their ClientProfile via email match."""
    Client = apps.get_model('devis', 'Client')
    ClientProfile = apps.get_model('clients', 'ClientProfile')
    User = apps.get_model('auth', 'User')

    # Build email → profile mapping
    profile_by_email = {}
    for profile in ClientProfile.objects.select_related('user').all():
        if profile.user and profile.user.email:
            profile_by_email[profile.user.email.lower()] = profile

    updated = 0
    for client in Client.objects.filter(linked_profile__isnull=True).iterator():
        if client.email:
            profile = profile_by_email.get(client.email.lower())
            if profile:
                client.linked_profile = profile
                client.save(update_fields=['linked_profile'])
                updated += 1

    if updated:
        print(f"  Linked {updated} Client(s) to their ClientProfile.")


def reverse_backfill(apps, schema_editor):
    """Reverse: clear all linked_profile FKs."""
    Client = apps.get_model('devis', 'Client')
    Client.objects.filter(linked_profile__isnull=False).update(linked_profile=None)


class Migration(migrations.Migration):

    dependencies = [
        ('devis', '0016_client_linked_profile'),
    ]

    operations = [
        migrations.RunPython(backfill_linked_profiles, reverse_backfill),
    ]
