"""Admin pour le portfolio."""
from django.contrib import admin
from .models import Project, ProjectImage
from .forms import ProjectAdminForm


class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 1


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    form = ProjectAdminForm
    list_display = ('title', 'project_type', 'client_name', 'is_featured', 'is_published', 'created_at')
    list_filter = ('project_type', 'is_featured', 'is_published')
    search_fields = ('title', 'client_name', 'objective')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('is_featured', 'is_published')
    ordering = ('-created_at',)
    inlines = [ProjectImageInline]
    
    fieldsets = (
        ('Identité du projet', {
            'fields': ('title', 'slug', 'project_type', 'client_name')
        }),
        ('Ch.01 — Pourquoi (Objectif)', {
            'description': 'Contexte du projet : pourquoi le client a fait appel à nous, quel était le besoin.',
            'fields': ('objective',)
        }),
        ('Ch.02 — Défi technique (Solution)', {
            'description': 'Le problème technique à résoudre et la solution conçue.',
            'fields': ('solution',)
        }),
        ('Ch.03 — Stratégie (Approche)', {
            'description': 'Méthodologie déployée, processus en phases, choix d\'architecture. Laissez vide pour afficher le texte par défaut.',
            'fields': ('strategy',)
        }),
        ('Ch.04 — Résultat (Impact)', {
            'description': 'Résultat final, impact mesurable, livrables.',
            'fields': ('result',)
        }),
        ('Stack technique', {
            'fields': ('technologies',)
        }),
        ('Médias', {
            'fields': ('thumbnail', 'url')
        }),
        ('Options', {
            'fields': ('is_featured', 'is_published')
        }),
    )


@admin.register(ProjectImage)
class ProjectImageAdmin(admin.ModelAdmin):
    list_display = ('project', 'caption', 'order')
    list_filter = ('project',)
    ordering = ('project', 'order')
