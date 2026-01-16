"""Admin pour les leads."""
from django.contrib import admin
from .models import Lead


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'project_type', 'budget', 'created_at')
    list_filter = ('project_type', 'budget', 'created_at')
    search_fields = ('name', 'email', 'message')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Contact', {
            'fields': ('name', 'email')
        }),
        ('Projet', {
            'fields': ('project_type', 'budget', 'message', 'existing_url', 'attachment')
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
