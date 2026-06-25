"""Models for the Simulateur app.

SimulatorReport : capture d'email en fin de parcours simulateur
pour envoi d'un rapport PDF personnalisé (lead generation).
"""
from __future__ import annotations

from django.db import models


class SimulatorReport(models.Model):
    """Demande de rapport PDF issu d'un simulateur.

    Stocke l'email du lead, le simulateur utilisé et un snapshot JSON
    des réponses / résultats. Un rapport PDF est généré et envoyé par email.
    """

    email = models.EmailField("Email", max_length=254)
    name = models.CharField("Nom", max_length=120, blank=True)
    company = models.CharField("Entreprise", max_length=180, blank=True)

    tool_slug = models.SlugField("Outil (slug)", max_length=64)
    tool_name = models.CharField("Outil (nom)", max_length=120)

    # Snapshot des inputs + résultats calculés côté front (Alpine).
    snapshot = models.JSONField("Données snapshot", default=dict, blank=True)

    # Anti-abus.
    ip_address = models.GenericIPAddressField("IP", null=True, blank=True)
    user_agent = models.CharField("User-Agent", max_length=500, blank=True)

    # État d'envoi.
    pdf_sent_at = models.DateTimeField("Envoyé le", null=True, blank=True)
    send_error = models.TextField("Erreur d'envoi", blank=True)
    send_attempts = models.PositiveSmallIntegerField(
        "Tentatives d'envoi", default=0,
        help_text="Incrémenté à chaque tentative ; plafonne les renvois du cron.",
    )

    # Conversion commerciale.
    converted_to_lead = models.ForeignKey(
        'leads.Lead',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='simulator_reports',
        verbose_name="Lead converti",
    )

    created_at = models.DateTimeField("Créé le", auto_now_add=True)

    class Meta:
        verbose_name = "Rapport simulateur"
        verbose_name_plural = "Rapports simulateur"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email'], name='idx_simreport_email'),
            models.Index(fields=['tool_slug'], name='idx_simreport_tool'),
            models.Index(fields=['created_at'], name='idx_simreport_created'),
        ]

    def __str__(self) -> str:
        return f"{self.email} – {self.tool_name}"
