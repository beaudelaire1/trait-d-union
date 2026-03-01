"""View definitions for the portfolio app."""
from __future__ import annotations

from typing import Any

from django.db.models import QuerySet
from django.http import HttpRequest
from django.views.generic import ListView, DetailView

from .models import Project, ProjectType


class ProjectListView(ListView):
    """List of projects with optional filtering by type."""

    model = Project
    template_name: str = 'portfolio/project_list.html'
    context_object_name: str = 'projects'

    def get_queryset(self) -> QuerySet[Project]:
        queryset = Project.objects.filter(is_published=True).defer('objective', 'solution', 'strategy', 'result')
        project_type = self.request.GET.get('type')
        if project_type in ProjectType.values:
            queryset = queryset.filter(project_type=project_type)
        return queryset

    def get_template_names(self) -> list[str]:
        # Only return partial for HTMX filter requests (when there's a target)
        # Full page navigation should return the complete template
        if self.request.headers.get('HX-Request') and self.request.headers.get('HX-Target') == 'project-list':
            return ['portfolio/_project_list_partial.html']
        return [self.template_name]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumbs_list'] = [
            {'name': 'Accueil', 'url': '/'},
            {'name': 'Portfolio', 'url': '/portfolio/'},
        ]
        return context


class ProjectDetailView(DetailView):
    """Detail page of a single project."""

    model = Project
    template_name: str = 'portfolio/project_detail.html'

    def get_queryset(self) -> QuerySet[Project]:
        return super().get_queryset().prefetch_related('strategy_phases', 'images')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        project = self.object
        context['breadcrumbs_list'] = [
            {'name': 'Accueil', 'url': '/'},
            {'name': 'Portfolio', 'url': '/portfolio/'},
            {'name': project.title, 'url': project.get_absolute_url()},
        ]
        return context