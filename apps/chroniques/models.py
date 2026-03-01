from __future__ import annotations

from django.db import models
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

User = get_user_model()


class Article(models.Model):
    """Article de Chroniques TUS."""

    title = models.CharField("Titre", max_length=200)
    slug = models.SlugField("Slug", max_length=200, unique=True)
    excerpt = models.TextField("Résumé", blank=True)
    body = models.TextField("Contenu")

    author = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Auteur"
    )
    cover_image = models.ImageField(
        upload_to="chroniques/covers/", blank=True, null=True, verbose_name="Image"
    )

    is_published = models.BooleanField("Publié", default=True)
    publish_date = models.DateTimeField("Date de publication", default=timezone.now)
    updated_at = models.DateTimeField("Mise à jour", auto_now=True)

    # 🔍 SEO: Dedicated meta description for search results
    meta_description = models.CharField(
        "Meta description",
        max_length=160,
        blank=True,
        help_text="Description pour Google (160 chars max). Si vide, utilise le résumé."
    )

    class Meta:
        ordering = ["-publish_date"]
        verbose_name = "Article"
        verbose_name_plural = "Articles"
        indexes = [
            models.Index(fields=['is_published', 'publish_date'], name='idx_article_pub'),
        ]

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self) -> str:
        return reverse("chroniques:detail", kwargs={"slug": self.slug})
