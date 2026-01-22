"""Admin configuration for the messaging app."""
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone

from .models import (
    Prospect,
    EmailTemplate,
    EmailCampaign,
    CampaignRecipient,
    ProspectMessage,
    ProspectActivity,
)


class ProspectActivityInline(admin.TabularInline):
    """Inline for prospect activities."""
    model = ProspectActivity
    extra = 0
    readonly_fields = ['activity_type', 'description', 'created_at']
    can_delete = False
    max_num = 10
    ordering = ['-created_at']


class ProspectMessageInline(admin.TabularInline):
    """Inline for prospect messages."""
    model = ProspectMessage
    extra = 0
    readonly_fields = ['direction', 'subject', 'status', 'created_at', 'opened_at']
    can_delete = False
    max_num = 5
    ordering = ['-created_at']
    fields = ['direction', 'subject', 'status', 'created_at', 'opened_at']


@admin.register(Prospect)
class ProspectAdmin(admin.ModelAdmin):
    """Admin for Prospect model."""
    
    list_display = [
        'contact_name',
        'company_name',
        'email',
        'sector',
        'status_badge',
        'priority_badge',
        'source',
        'last_contacted_at',
        'created_at',
    ]
    list_filter = ['status', 'source', 'sector', 'priority', 'created_at']
    search_fields = ['contact_name', 'company_name', 'email', 'notes', 'tags']
    date_hierarchy = 'created_at'
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = [
        ('Informations de contact', {
            'fields': [
                ('contact_name', 'company_name'),
                ('email', 'phone'),
                'website',
            ]
        }),
        ('Activité', {
            'fields': [
                ('sector', 'activity_description'),
                'pain_points',
            ]
        }),
        ('CRM', {
            'fields': [
                ('status', 'source'),
                'priority',
                ('last_contacted_at', 'next_follow_up'),
            ]
        }),
        ('Notes & Tags', {
            'fields': ['notes', 'tags'],
            'classes': ['collapse'],
        }),
        ('Métadonnées', {
            'fields': [('created_at', 'updated_at'), 'converted_to_client'],
            'classes': ['collapse'],
        }),
    ]
    
    inlines = [ProspectMessageInline, ProspectActivityInline]
    
    actions = ['mark_as_contacted', 'mark_as_interested', 'send_prospection_email']
    
    def status_badge(self, obj):
        """Display status as a colored badge."""
        colors = {
            'new': '#3B82F6',
            'contacted': '#F59E0B',
            'interested': '#22C55E',
            'meeting': '#8B5CF6',
            'proposal': '#EC4899',
            'negotiation': '#F97316',
            'converted': '#10B981',
            'lost': '#EF4444',
            'not_interested': '#6B7280',
        }
        color = colors.get(obj.status, '#6B7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; '
            'border-radius: 4px; font-size: 11px; font-weight: 600;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Statut'
    status_badge.admin_order_field = 'status'
    
    def priority_badge(self, obj):
        """Display priority as stars."""
        stars = '★' * (6 - obj.priority) + '☆' * (obj.priority - 1)
        color = '#EF4444' if obj.priority <= 2 else '#F59E0B' if obj.priority == 3 else '#6B7280'
        return format_html(
            '<span style="color: {}; font-size: 14px;">{}</span>',
            color,
            stars
        )
    priority_badge.short_description = 'Priorité'
    priority_badge.admin_order_field = 'priority'
    
    @admin.action(description="Marquer comme contacté")
    def mark_as_contacted(self, request, queryset):
        queryset.update(status='contacted', last_contacted_at=timezone.now())
        self.message_user(request, f"{queryset.count()} prospect(s) marqué(s) comme contacté(s).")
    
    @admin.action(description="Marquer comme intéressé")
    def mark_as_interested(self, request, queryset):
        queryset.update(status='interested')
        self.message_user(request, f"{queryset.count()} prospect(s) marqué(s) comme intéressé(s).")
    
    @admin.action(description="📧 Envoyer email de prospection")
    def send_prospection_email(self, request, queryset):
        # This will be implemented with the email service
        self.message_user(request, f"Fonctionnalité à implémenter pour {queryset.count()} prospect(s).")


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    """Admin for EmailTemplate model."""
    
    list_display = ['name', 'category', 'subject', 'is_active', 'updated_at']
    list_filter = ['category', 'is_active']
    search_fields = ['name', 'subject', 'html_template']
    prepopulated_fields = {'slug': ('name',)}
    
    fieldsets = [
        (None, {
            'fields': ['name', 'slug', 'category', 'is_active']
        }),
        ('Contenu', {
            'fields': ['subject', 'html_template', 'text_content']
        }),
    ]


class CampaignRecipientInline(admin.TabularInline):
    """Inline for campaign recipients."""
    model = CampaignRecipient
    extra = 0
    readonly_fields = ['status', 'sent_at', 'opened_at', 'clicked_at', 'replied_at']
    raw_id_fields = ['prospect']


@admin.register(EmailCampaign)
class EmailCampaignAdmin(admin.ModelAdmin):
    """Admin for EmailCampaign model."""
    
    list_display = [
        'name',
        'template',
        'status_badge',
        'recipient_count',
        'stats_display',
        'scheduled_at',
        'created_at',
    ]
    list_filter = ['status', 'template__category', 'created_at']
    search_fields = ['name']
    date_hierarchy = 'created_at'
    raw_id_fields = ['template', 'created_by']
    
    fieldsets = [
        (None, {
            'fields': ['name', 'template', 'status']
        }),
        ('Planification', {
            'fields': ['scheduled_at', ('started_at', 'completed_at')]
        }),
        ('Statistiques', {
            'fields': [
                ('total_sent', 'total_opened'),
                ('total_clicked', 'total_replied'),
            ],
            'classes': ['collapse'],
        }),
    ]
    
    inlines = [CampaignRecipientInline]
    
    def status_badge(self, obj):
        """Display status as a colored badge."""
        colors = {
            'draft': '#6B7280',
            'scheduled': '#3B82F6',
            'sending': '#F59E0B',
            'sent': '#22C55E',
            'paused': '#EF4444',
        }
        color = colors.get(obj.status, '#6B7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; '
            'border-radius: 4px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Statut'
    
    def recipient_count(self, obj):
        """Display recipient count."""
        return obj.recipients.count()
    recipient_count.short_description = 'Destinataires'
    
    def stats_display(self, obj):
        """Display campaign stats."""
        if obj.total_sent == 0:
            return '-'
        return format_html(
            '📧 {} | 👁 {}% | 🖱 {}%',
            obj.total_sent,
            obj.open_rate,
            obj.click_rate
        )
    stats_display.short_description = 'Stats'


@admin.register(ProspectMessage)
class ProspectMessageAdmin(admin.ModelAdmin):
    """Admin for ProspectMessage model."""
    
    list_display = [
        'direction_icon',
        'prospect',
        'subject',
        'status_badge',
        'created_at',
        'opened_at',
    ]
    list_filter = ['direction', 'status', 'created_at']
    search_fields = ['subject', 'content', 'prospect__email', 'prospect__contact_name']
    date_hierarchy = 'created_at'
    raw_id_fields = ['prospect']
    
    def direction_icon(self, obj):
        """Display direction as an icon."""
        if obj.direction == 'outbound':
            return format_html('<span style="font-size: 18px;">📤</span>')
        return format_html('<span style="font-size: 18px;">📥</span>')
    direction_icon.short_description = ''
    
    def status_badge(self, obj):
        """Display status as a colored badge."""
        colors = {
            'draft': '#6B7280',
            'pending': '#F59E0B',
            'sent': '#3B82F6',
            'delivered': '#22C55E',
            'opened': '#8B5CF6',
            'clicked': '#EC4899',
            'replied': '#10B981',
            'failed': '#EF4444',
            'received': '#3B82F6',
        }
        color = colors.get(obj.status, '#6B7280')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 4px 8px; '
            'border-radius: 4px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Statut'


@admin.register(ProspectActivity)
class ProspectActivityAdmin(admin.ModelAdmin):
    """Admin for ProspectActivity model."""
    
    list_display = ['prospect', 'activity_type', 'description', 'created_at']
    list_filter = ['activity_type', 'created_at']
    search_fields = ['description', 'prospect__email', 'prospect__contact_name']
    date_hierarchy = 'created_at'
    raw_id_fields = ['prospect']
