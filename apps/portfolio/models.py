"""Models for the portfolio app."""
from __future__ import annotations

from django.db import models


class ProjectType(models.TextChoices):
    """Types of projects for filtering."""

    SITE = 'site', 'Site'
    COMMERCE = 'commerce', 'Commerce'
    OUTILS = 'outils', 'Outils métiers'


class Project(models.Model):
    """Represents a completed project for the portfolio."""

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    project_type = models.CharField(max_length=20, choices=ProjectType.choices)
    client_name = models.CharField(max_length=200, blank=True)
    objective = models.TextField(help_text="Ch.01 — Pourquoi. Markdown supporté : **gras**, *italique*, - liste à puces")
    solution = models.TextField(help_text="Ch.02 — Défi technique. Markdown supporté : **gras**, *italique*, - liste à puces")
    strategy = models.TextField(blank=True, default='', help_text="Ch.03 — Stratégie. Markdown supporté : **gras**, *italique*, - liste à puces")
    result = models.TextField(help_text="Ch.04 — Résultat. Markdown supporté : **gras**, *italique*, - liste à puces")
    image_ch02 = models.ImageField(upload_to='portfolio/chapters/', blank=True, null=True, help_text="Image Ch.02 — capture code ou maquette (1200×750 px idéal)")
    image_ch03 = models.ImageField(upload_to='portfolio/chapters/', blank=True, null=True, help_text="Image Ch.03 — architecture ou schéma (1920×820 px idéal)")
    image_ch04 = models.ImageField(upload_to='portfolio/chapters/', blank=True, null=True, help_text="Image Ch.04 — capture du résultat final (1920×1080 px idéal)")
    technologies = models.JSONField(default=list, blank=True)
    thumbnail = models.ImageField(upload_to='portfolio/thumbnails/', blank=True, null=True)
    url = models.URLField(blank=True)
    is_featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

        indexes = [
            models.Index(fields=['is_published', '-created_at'], name='idx_portfolio_published'),
            models.Index(fields=['project_type', 'is_published'], name='idx_portfolio_type'),
        ]

    def __str__(self) -> str:
        return self.title

    def get_absolute_url(self) -> str:
        from django.urls import reverse
        return reverse('portfolio:detail', kwargs={'slug': self.slug})

    def tech_list(self) -> list[str]:
        """Return normalized list of technologies regardless of stored JSON shape.

        Supports list[str], comma-separated string, or dict with common keys
        like 'technologies', 'stack', 'modules_cles', 'modules', 'tech', 'tags'.
        """
        t = self.technologies
        if isinstance(t, dict):
            candidates: list[str] = []
            for key in ('stack', 'technologies', 'modules_cles', 'modules', 'tech', 'tags'):
                v = t.get(key)
                if isinstance(v, list):
                    candidates += [str(x) for x in v]
                elif isinstance(v, str):
                    candidates += [s.strip() for s in v.split(',')]
            if not candidates:
                for v in t.values():
                    if isinstance(v, list):
                        candidates += [str(x) for x in v]
                    elif isinstance(v, str):
                        candidates += [s.strip() for s in v.split(',')]
            return [x for x in candidates if x]
        if isinstance(t, list):
            return [str(x) for x in t]
        if isinstance(t, str):
            return [s.strip() for s in t.split(',')]
        return []


class ProjectImage(models.Model):
    """Additional images for a project."""

    project = models.ForeignKey(Project, related_name='images', on_delete=models.CASCADE)
    image = models.ImageField(upload_to='portfolio/images/')
    caption = models.CharField(max_length=255, blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self) -> str:
        return f"{self.project.title} image {self.order}"


class StrategyPhaseIcon(models.TextChoices):
    """Icônes prédéfinies pour les phases de stratégie."""

    SEARCH = 'search', '🔍 Analyse / Audit'
    ARCHITECTURE = 'architecture', '📦 Architecture / Conception'
    DEPLOY = 'deploy', '✦ Déploiement / Livraison'
    CODE = 'code', '💻 Code / Développement'
    DESIGN = 'design', '🎨 Design / UX'
    DATABASE = 'database', '🗄️ Base de données'
    SECURITY = 'security', '🔒 Sécurité'
    PERFORMANCE = 'performance', '⚡ Performance'
    TEST = 'test', '✅ Tests / QA'
    MEETING = 'meeting', '🤝 Échange / Cadrage'


class StrategyPhase(models.Model):
    """Phase de stratégie pour le Ch.03 d'un projet portfolio."""

    project = models.ForeignKey(
        Project,
        related_name='strategy_phases',
        on_delete=models.CASCADE,
    )
    phase_label = models.CharField(
        max_length=100,
        help_text="Ex : Phase d'audit, Phase de conception, Phase de livraison",
    )
    title = models.CharField(
        max_length=200,
        help_text='Ex : Analyse & Exploration, Architecture & Prototypage',
    )
    description = models.TextField(
        help_text='Description de cette phase (2-3 phrases).',
    )
    icon = models.CharField(
        max_length=20,
        choices=StrategyPhaseIcon.choices,
        default=StrategyPhaseIcon.SEARCH,
        help_text='Icône affichée à côté de la phase.',
    )
    order = models.PositiveIntegerField(
        default=0,
        help_text="Ordre d'affichage (0 = premier).",
    )

    class Meta:
        ordering = ['order']
        verbose_name = 'Phase de stratégie'
        verbose_name_plural = 'Phases de stratégie'

    def __str__(self) -> str:
        return f"{self.project.title} — {self.phase_label}: {self.title}"