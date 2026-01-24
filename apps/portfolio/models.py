"""Models for the portfolio app."""
from __future__ import annotations

from django.db import models


class ProjectType(models.TextChoices):
    """Types of projects for filtering."""

    VITRINE = 'vitrine', 'Site Vitrine'
    COMMERCE = 'commerce', 'E‑commerce'
    SYSTEME = 'systeme', 'Plateforme / Mini‑ERP'


class Project(models.Model):
    """Represents a completed project for the portfolio."""

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    project_type = models.CharField(max_length=20, choices=ProjectType.choices)
    client_name = models.CharField(max_length=200, blank=True)
    objective = models.TextField()
    solution = models.TextField()
    result = models.TextField()
    technologies = models.JSONField(default=list, blank=True)
    thumbnail = models.ImageField(upload_to='portfolio/thumbnails/', blank=True, null=True)
    url = models.URLField(blank=True)
    is_featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

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