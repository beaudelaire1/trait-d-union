"""Admin configuration for the pages app."""
from django.contrib import admin
from django.utils.html import format_html

from .models import Testimonial, SimulatorQuotaUsage


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    """Admin interface for testimonials."""
    
    list_display = ['client_name', 'company_name', 'rating', 'is_published', 'order', 'created_at']
    list_filter = ['is_published', 'rating', 'created_at']
    search_fields = ['client_name', 'company_name', 'content']
    list_editable = ['is_published', 'order']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Informations client', {
            'fields': ('client_name', 'company_name', 'position', 'avatar')
        }),
        ('Témoignage', {
            'fields': ('content', 'rating')
        }),
        ('Publication', {
            'fields': ('is_published', 'order')
        }),
    )


@admin.register(SimulatorQuotaUsage)
class SimulatorQuotaUsageAdmin(admin.ModelAdmin):
    """Admin interface for simulator quota tracking."""
    
    list_display = ['ip_address', 'user_agent_display', 'generation_count', 'quota_status', 'last_generation', 'created_at']
    list_filter = ['generation_count', 'last_generation', 'created_at']
    search_fields = ['ip_address', 'user_agent']
    readonly_fields = ['user_agent_hash', 'created_at', 'last_generation']
    date_hierarchy = 'last_generation'
    ordering = ['-last_generation']
    
    fieldsets = (
        ('Identification', {
            'fields': ('ip_address', 'user_agent', 'user_agent_hash')
        }),
        ('Quota', {
            'fields': ('generation_count', 'last_generation', 'created_at')
        }),
    )
    
    def user_agent_display(self, obj):
        """Truncate User-Agent for display."""
        ua = obj.user_agent[:60]
        if len(obj.user_agent) > 60:
            ua += '...'
        return ua
    user_agent_display.short_description = 'User-Agent'
    
    def quota_status(self, obj):
        """Visual indicator of quota status."""
        if obj.is_quota_exceeded():
            return format_html('<span style="color: red; font-weight: bold;">⚠️ DÉPASSÉ</span>')
        elif obj.generation_count >= 4:
            return format_html('<span style="color: orange;">⚡ {}/5</span>', obj.generation_count)
        return format_html('<span style="color: green;">✓ {}/5</span>', obj.generation_count)
    quota_status.short_description = 'Quota'
