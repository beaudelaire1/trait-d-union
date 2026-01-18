"""Models for the leads app (contact requests)."""
from __future__ import annotations

from django.db import models


class ProjectTypeChoice(models.TextChoices):
    VITRINE = 'vitrine', 'Site Vitrine'
    ECOMMERCE = 'ecommerce', 'E‑commerce'
    PLATEFORME = 'plateforme', 'Plateforme / Mini‑ERP'


class BudgetRange(models.TextChoices):
    SMALL = 'small', '< 3 000 €'
    MEDIUM = 'medium', '3 000 € – 8 000 €'
    LARGE = 'large', '8 000 € – 15 000 €'
    ENTERPRISE = 'enterprise', '> 15 000 €'
    DISCUSS = 'discuss', 'À discuter'


class Lead(models.Model):
    """Represents a contact request from the website."""

    name = models.CharField("Nom complet", max_length=100)
    email = models.EmailField("Email", max_length=254)
    project_type = models.CharField("Type de projet", max_length=20, choices=ProjectTypeChoice.choices)
    message = models.TextField("Message")
    budget = models.CharField("Budget estimé", max_length=20, choices=BudgetRange.choices, blank=True)
    existing_url = models.URLField("Site existant", max_length=500, blank=True)
    attachment = models.FileField("Pièce jointe", upload_to='leads/attachments/', blank=True)
    honeypot = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_processed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']

    def __str__(self) -> str:
        return f"{self.name} – {self.project_type}"