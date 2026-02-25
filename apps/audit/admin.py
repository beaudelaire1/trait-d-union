"""Admin pour le module audit."""
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    """Admin read-only pour le journal d'audit."""
    
    list_display = [
        'timestamp_display',
        'action_type_display',
        'content_type',
        'object_id',
        'actor_display',
    ]
    list_filter = ['action_type', 'timestamp', 'actor']
    search_fields = ['description', 'content_type', 'actor__email', 'actor__username']
    readonly_fields = [
        'timestamp',
        'action_type',
        'actor',
        'content_type',
        'object_id',
        'metadata',
        'description',
    ]
    
    def has_add_permission(self, request):
        """Audit logs ne peuvent pas être créés manuellement."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Audit logs ne peuvent pas être supprimés."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Audit logs ne peuvent pas être édités."""
        return False
    
    def timestamp_display(self, obj: AuditLog) -> str:
        """Affiche le timestamp avec formatage."""
        return obj.timestamp.strftime("%d/%m/%Y %H:%M:%S")
    timestamp_display.short_description = "Horodatage"
    
    def action_type_display(self, obj: AuditLog) -> str:
        """Affiche l'action avec couleur."""
        action_label = obj.get_action_type_display()
        color_map = {
            'quote': '#0066cc',
            'invoice': '#00aa00',
            'milestone': '#ff6600',
            'client': '#9900cc',
        }
        color = next(
            (c for k, c in color_map.items() if k in obj.action_type),
            '#666666'
        )
        return format_html(
            '<span style="background-color:{}; color:white; padding:3px 8px; border-radius:3px;">{}</span>',
            color,
            action_label
        )
    action_type_display.short_description = "Action"
    
    def actor_display(self, obj: AuditLog) -> str:
        """Affiche l'acteur ou "système"."""
        if obj.actor:
            return f"{obj.actor.username} ({obj.actor.email})"
        return "Système"
    actor_display.short_description = "Acteur"
    
    def get_queryset(self, request):
        """Optimiser les requêtes."""
        return super().get_queryset(request).select_related('actor').order_by('-timestamp')
