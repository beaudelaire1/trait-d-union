"""Modèle pour les diagnostics de sites web — outil interne TUS."""
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _


class SiteDiagnostic(models.Model):
    """Diagnostic complet d'un site web client — outil interne staff uniquement."""

    class Status(models.TextChoices):
        PENDING = "pending", _("En attente")
        RUNNING = "running", _("En cours")
        COMPLETED = "completed", _("Terminé")
        FAILED = "failed", _("Échoué")

    url = models.URLField(_("URL du site"), max_length=500)
    created_at = models.DateTimeField(_("Date"), auto_now_add=True, db_index=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name="site_diagnostics", verbose_name=_("Lancé par"),
    )
    status = models.CharField(
        _("Statut"), max_length=20,
        choices=Status.choices, default=Status.PENDING,
    )
    overall_score = models.PositiveSmallIntegerField(_("Score global"), default=0)
    results = models.JSONField(_("Résultats"), default=dict, blank=True)
    duration_seconds = models.FloatField(_("Durée (s)"), default=0)
    error_message = models.TextField(_("Erreur"), blank=True)

    class Meta:
        verbose_name = _("Diagnostic de site")
        verbose_name_plural = _("Diagnostics de sites")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Diag {self.url} — {self.overall_score}/100 ({self.get_status_display()})"

    @property
    def score_color(self):
        if self.overall_score >= 80:
            return "#30d158"
        if self.overall_score >= 50:
            return "#ff9f0a"
        return "#ff453a"
