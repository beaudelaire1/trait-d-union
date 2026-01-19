"""Admin pour les leads."""
from django.contrib import admin
from django.utils.html import format_html
from .models import Lead


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'project_type', 'budget', 'attachment_link', 'created_at')
    list_filter = ('project_type', 'budget', 'created_at', ('attachment', admin.EmptyFieldListFilter))
    search_fields = ('name', 'email', 'message')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    def attachment_link(self, obj):
        if obj.attachment:
            return format_html('<a href="{}" target="_blank" class="button">Télécharger</a>', obj.attachment.url)
        return "-"
    attachment_link.short_description = "Pièce jointe"
    attachment_link.allow_tags = True

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
