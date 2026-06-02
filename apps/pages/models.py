"""Models for the pages app."""
from django.db import models


class TestimonialSource(models.TextChoices):
    """Origine d'un témoignage affiché sur le site."""

    MANUAL = "manual", "Saisie manuelle (admin)"
    GOOGLE = "google", "Google Business Profile"


class Testimonial(models.Model):
    """Témoignage client affiché sur la page d'accueil et la page dédiée.

    Deux sources possibles (champ ``source``) :

    - ``manual`` : saisi à la main dans l'admin Django.
    - ``google`` : synchronisé automatiquement depuis Google Places API
      via ``manage.py sync_google_reviews``. La clé d'unicité est
      l'identifiant ``google_review_id`` pour permettre l'UPSERT.
    """

    # ── Identité auteur ─────────────────────────────────────────
    client_name = models.CharField("Nom du client", max_length=200)
    company_name = models.CharField("Nom de l'entreprise", max_length=200, blank=True)
    position = models.CharField("Poste", max_length=100, blank=True)

    # ── Contenu ─────────────────────────────────────────────────
    content = models.TextField("Témoignage")
    avatar = models.ImageField("Photo", upload_to="testimonials/", blank=True, null=True)
    avatar_url = models.URLField(
        "Photo distante (Google)",
        max_length=500, blank=True,
        help_text="Avatar hébergé chez Google. Prioritaire sur le champ avatar uploadé si renseigné.",
    )
    rating = models.PositiveSmallIntegerField("Note", default=5, help_text="Note sur 5")

    # ── Provenance ──────────────────────────────────────────────
    source = models.CharField(
        "Source",
        max_length=16,
        choices=TestimonialSource.choices,
        default=TestimonialSource.MANUAL,
        db_index=True,
    )
    google_review_id = models.CharField(
        "Identifiant Google",
        max_length=255, blank=True, db_index=True,
        help_text="Identifiant unique fourni par Google (champ `name`). Vide pour les avis manuels.",
    )
    review_url = models.URLField(
        "Lien vers l'avis",
        max_length=500, blank=True,
        help_text="URL publique de l'avis (Google) si disponible.",
    )
    review_published_at = models.DateTimeField(
        "Publié le", null=True, blank=True,
        help_text="Date de publication chez la source (Google) si connue.",
    )
    last_synced_at = models.DateTimeField(
        "Dernière synchro", null=True, blank=True,
        help_text="Mis à jour automatiquement à chaque exécution de `sync_google_reviews`.",
    )

    # ── Pilotage éditorial ──────────────────────────────────────
    is_published = models.BooleanField("Publié", default=True)
    order = models.PositiveIntegerField("Ordre d'affichage", default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "-review_published_at", "-created_at"]
        verbose_name = "Témoignage"
        verbose_name_plural = "Témoignages"
        constraints = [
            # Unicité forte sur l'ID Google (évite les doublons à la synchro)
            models.UniqueConstraint(
                fields=["google_review_id"],
                condition=models.Q(google_review_id__gt=""),
                name="unique_google_review_id",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.client_name} - {self.company_name or 'Particulier'}"

    @property
    def display_avatar(self) -> str:
        """URL d'avatar à afficher dans le template (priorité Google si présent)."""
        if self.avatar_url:
            return self.avatar_url
        if self.avatar:
            return self.avatar.url
        return ""
