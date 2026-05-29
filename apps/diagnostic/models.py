"""Modèle pour les diagnostics de sites web — outil interne TUS."""
from django.contrib.auth.models import User
from django.db import models
from django.utils.translation import gettext_lazy as _

from .field_questions import SECTORS


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


class FieldDiagnostic(models.Model):
    """Diagnostic terrain d'une entreprise — entretien client structuré.

    Contrairement au :class:`SiteDiagnostic` (analyse automatique d'une URL),
    ce diagnostic repose sur des réponses saisies pendant un entretien. Le
    questionnaire est orienté par le ``profile`` choisi en amont et le moteur
    de scoring produit un score objectif /100, des signaux et un plan d'action.
    """

    class Profile(models.TextChoices):
        SOLO = "solo", _("Indépendant / Freelance")
        TPE = "tpe", _("TPE · 1 à 9 salariés")
        PME = "pme", _("PME · 10 à 50 personnes")
        CROISSANCE = "croissance", _("Forte croissance / Scale-up")
        REPRISE = "reprise", _("Création / reprise récente")
        STRATEGIQUE = "strategique", _("Réflexion stratégique")

    company_name = models.CharField(_("Entreprise"), max_length=200)
    sector = models.CharField(
        _("Secteur"), max_length=50, blank=True, choices=SECTORS,
    )
    profile = models.CharField(
        _("Profil"), max_length=20,
        choices=Profile.choices, default=Profile.PME,
    )
    contact_name = models.CharField(_("Interlocuteur"), max_length=200, blank=True)
    contact_email = models.EmailField(_("Email"), blank=True)
    notes = models.TextField(_("Notes d'entretien"), blank=True)

    created_at = models.DateTimeField(_("Date"), auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(_("Mis à jour"), auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name="field_diagnostics", verbose_name=_("Réalisé par"),
    )

    overall_score = models.PositiveSmallIntegerField(_("Score global"), default=0)
    answers = models.JSONField(_("Réponses"), default=dict, blank=True)
    results = models.JSONField(_("Analyse"), default=dict, blank=True)

    class Meta:
        verbose_name = _("Diagnostic terrain")
        verbose_name_plural = _("Diagnostics terrain")
        ordering = ["-created_at"]

    def __str__(self):
        return f"Diag terrain {self.company_name} — {self.overall_score}/100"

    @property
    def score_color(self):
        if self.overall_score >= 80:
            return "#30d158"
        if self.overall_score >= 60:
            return "#9acd32"
        if self.overall_score >= 40:
            return "#ff9f0a"
        return "#ff453a"
