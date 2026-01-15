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
        queryset = Project.objects.filter(is_published=True)
        project_type = self.request.GET.get('type')
        if project_type in ProjectType.values:
            queryset = queryset.filter(project_type=project_type)
        return queryset

    def get_template_names(self) -> list[str]:
        # If the request comes from HTMX, return partial template for list only
        if self.request.headers.get('HX-Request'):
            return ['portfolio/_project_list_partial.html']
        return [self.template_name]


class ProjectDetailView(DetailView):
    """Detail page of a single project."""

    model = Project
    template_name: str = 'portfolio/project_detail.html'