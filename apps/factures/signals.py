
from __future__ import annotations

import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Invoice

logger = logging.getLogger(__name__)


# Notification de création de facture gérée dans apps/clients/signals.py
# pour éviter les doublons.
