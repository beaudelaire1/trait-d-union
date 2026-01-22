"""Models for email composition and templates."""
from __future__ import annotations

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailTemplateCategory(models.TextChoices):
    """Categories of email templates."""
    PROSPECTION = 'prospection', 'Prospection'
    REMERCIEMENT = 'remerciement', 'Remerciement'
    RELANCE = 'relance', 'Relance'
    PROPOSITION = 'proposition', 'Proposition commerciale'
    CONFIRMATION = 'confirmation', 'Confirmation de rendez-vous'
    SUIVI = 'suivi', 'Suivi de projet'


class EmailTemplate(models.Model):
    """Pre-defined email templates."""
    
    name = models.CharField("Nom du template", max_length=100)
    category = models.CharField(
        "Catégorie", 
        max_length=20, 
        choices=EmailTemplateCategory.choices
    )
    subject = models.CharField("Sujet", max_length=200)
    body_html = models.TextField("Corps HTML")
    is_active = models.BooleanField("Actif", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category', 'name']
        verbose_name = "Template d'email"
        verbose_name_plural = "Templates d'email"
    
    def __str__(self) -> str:
        return f"{self.get_category_display()} - {self.name}"


class EmailComposition(models.Model):
    """Represents an email being composed or sent."""
    
    to_emails = models.TextField("Destinataires (To)", help_text="Séparés par des virgules")
    cc_emails = models.TextField("CC", blank=True, help_text="Séparés par des virgules")
    bcc_emails = models.TextField("BCC", blank=True, help_text="Séparés par des virgules")
    subject = models.CharField("Sujet", max_length=500)
    body_html = models.TextField("Corps HTML")
    template_used = models.ForeignKey(
        EmailTemplate, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        verbose_name="Template utilisé"
    )
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        verbose_name="Créé par"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField("Envoyé le", null=True, blank=True)
    is_draft = models.BooleanField("Brouillon", default=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Email"
        verbose_name_plural = "Emails"
    
    def __str__(self) -> str:
        status = "Brouillon" if self.is_draft else "Envoyé"
        return f"{status} - {self.subject[:50]}"
    
    def get_to_list(self) -> list[str]:
        """Return list of TO email addresses."""
        return [email.strip() for email in self.to_emails.split(',') if email.strip()]
    
    def get_cc_list(self) -> list[str]:
        """Return list of CC email addresses."""
        if not self.cc_emails:
            return []
        return [email.strip() for email in self.cc_emails.split(',') if email.strip()]
    
    def get_bcc_list(self) -> list[str]:
        """Return list of BCC email addresses."""
        if not self.bcc_emails:
            return []
        return [email.strip() for email in self.bcc_emails.split(',') if email.strip()]
