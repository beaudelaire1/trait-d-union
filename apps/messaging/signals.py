"""Signals for the messaging app."""
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Prospect, ProspectActivity


@receiver(post_save, sender=Prospect)
def log_prospect_creation(sender, instance, created, **kwargs):
    """Log activity when a prospect is created."""
    if created:
        ProspectActivity.objects.create(
            prospect=instance,
            activity_type='created',
            description=f"Prospect créé: {instance.contact_name}",
        )
