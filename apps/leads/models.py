"""Models for the leads app (contact requests)."""
from __future__ import annotations

from django.core.validators import FileExtensionValidator
from django.db import models
from core.utils import raw_media_storage


from phonenumber_field.modelfields import PhoneNumberField

class ProjectTypeChoice(models.TextChoices):
    SITE = 'site', 'Site'
    COMMERCE = 'commerce', 'Commerce'
    OUTILS_METIER = 'outils_metier', 'Outils métier'
    OTHER = 'other', 'Autre'


class BudgetRange(models.TextChoices):
    SMALL = 'small', '< 3 000 €'
    MEDIUM = 'medium', '3 000 € – 8 000 €'
    LARGE = 'large', '8 000 € – 15 000 €'
    ENTERPRISE = 'enterprise', '> 15 000 €'
    DISCUSS = 'discuss', 'À discuter'


class LeadStatus(models.TextChoices):
    NEW = 'new', '🆕 Nouveau'
    CONTACTED = 'contacted', '📧 Contacté'
    QUALIFIED = 'qualified', '✅ Qualifié'
    CONVERTED = 'converted', '🎉 Converti'
    LOST = 'lost', '❌ Perdu'


class Lead(models.Model):
    """Represents a contact request from the website."""

    name = models.CharField("Nom complet", max_length=100)
    email = models.EmailField("Email", max_length=254)
    phone = PhoneNumberField("Téléphone", blank=True)
    project_type = models.CharField("Type de projet", max_length=20, choices=ProjectTypeChoice.choices)
    message = models.TextField("Message")
    budget = models.CharField("Budget estimé", max_length=20, choices=BudgetRange.choices, blank=True)
    existing_url = models.URLField("Site existant", max_length=500, blank=True)
    attachment = models.FileField(
        "Pièce jointe",
        upload_to='leads/attachments/',
        blank=True,
        storage=raw_media_storage,
        validators=[
            FileExtensionValidator(
                allowed_extensions=['pdf', 'doc', 'docx', 'xls', 'xlsx',
                                    'jpg', 'jpeg', 'png', 'webp', 'zip'],
            ),
        ],
    )
    honeypot = models.CharField(max_length=255, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_processed = models.BooleanField(default=False)

    # --- Suivi pipeline ---
    status = models.CharField(
        "Statut", max_length=20,
        choices=LeadStatus.choices, default=LeadStatus.NEW,
    )
    converted_to_client = models.ForeignKey(
        'clients.ClientProfile',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='converted_leads',
        verbose_name="Client converti",
    )
    converted_at = models.DateTimeField("Date de conversion", null=True, blank=True)
    notes = models.TextField("Notes internes", blank=True)

    # --- Scoring automatique ---
    score = models.PositiveSmallIntegerField(
        "Score", default=0,
        help_text="Score automatique 0-100 basé sur budget, type de projet et complétude.",
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Lead"
        verbose_name_plural = "Leads"
        indexes = [
            models.Index(fields=['status'], name='idx_lead_status'),
        ]

    def __str__(self) -> str:
        return f"{self.name} – {self.project_type}"

    @property
    def is_converted(self) -> bool:
        return self.converted_to_client_id is not None

    def compute_score(self) -> int:
        """Calcule un score 0-100 basé sur le profil du lead.

        Critères :
        - Budget (0-40 pts) : enterprise=40, large=30, medium=20, small=10, discuss=15
        - Type de projet (0-25 pts) : outils_metier=25, commerce=20, site=15, other=10
        - Complétude (0-20 pts) : téléphone=10, site existant=5, pièce jointe=5
        - Message (0-15 pts) : longueur > 100 chars = 15, > 50 = 10, sinon 5
        """
        s = 0
        # Budget
        budget_scores = {'enterprise': 40, 'large': 30, 'medium': 20, 'discuss': 15, 'small': 10}
        s += budget_scores.get(self.budget, 0)
        # Type
        type_scores = {'outils_metier': 25, 'commerce': 20, 'site': 15, 'other': 10}
        s += type_scores.get(self.project_type, 10)
        # Complétude
        if self.phone:
            s += 10
        if self.existing_url:
            s += 5
        if self.attachment:
            s += 5
        # Message
        msg_len = len(self.message or '')
        if msg_len > 100:
            s += 15
        elif msg_len > 50:
            s += 10
        else:
            s += 5
        return min(s, 100)


class EmailSubscriber(models.Model):
    """Abonné à la newsletter / lead magnet.

    Capture d'emails depuis :
    - Footer (toutes les pages)
    - Fin d'article (chroniques)
    - Simulateurs (rapport PDF)
    """

    class Source(models.TextChoices):
        FOOTER = 'footer', 'Footer'
        ARTICLE = 'article', 'Fin d\'article'
        SIMULATEUR = 'simulateur', 'Simulateur'
        POPUP = 'popup', 'Popup'

    email = models.EmailField("Email", unique=True)
    source = models.CharField(
        "Source", max_length=20,
        choices=Source.choices, default=Source.FOOTER,
    )
    source_detail = models.CharField(
        "Détail source", max_length=200, blank=True,
        help_text="Slug article, nom simulateur, etc.",
    )
    is_confirmed = models.BooleanField("Confirmé", default=False)
    is_active = models.BooleanField("Actif", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = "Abonné newsletter"
        verbose_name_plural = "Abonnés newsletter"
        indexes = [
            models.Index(fields=['is_active', '-created_at'], name='idx_subscriber_active'),
        ]

    def __str__(self) -> str:
        return f"{self.email} ({self.get_source_display()})"


# Auto-compute lead score on save
from django.db.models.signals import pre_save
from django.dispatch import receiver


@receiver(pre_save, sender=Lead)
def auto_score_lead(sender, instance, **kwargs):
    """Compute lead score before saving."""
    instance.score = instance.compute_score()
