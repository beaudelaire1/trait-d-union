"""Admin pour les leads."""
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from .models import Lead
from .email_models import EmailTemplate, EmailComposition


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


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_active', 'created_at')
    list_filter = ('category', 'is_active', 'created_at')
    search_fields = ('name', 'subject', 'body_html')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('category', 'name')
    
    fieldsets = (
        ('Informations', {
            'fields': ('name', 'category', 'is_active')
        }),
        ('Contenu', {
            'fields': ('subject', 'body_html')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(EmailComposition)
class EmailCompositionAdmin(admin.ModelAdmin):
    list_display = ('subject', 'status_badge', 'to_emails_short', 'created_by', 'created_at', 'compose_link')
    list_filter = ('is_draft', 'created_at', 'sent_at')
    search_fields = ('subject', 'to_emails', 'body_html')
    readonly_fields = ('created_at', 'sent_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    change_list_template = 'admin/leads/emailcomposition/change_list.html'
    
    def status_badge(self, obj):
        if obj.is_draft:
            return format_html('<span style="color: orange;">📝 Brouillon</span>')
        return format_html('<span style="color: green;">✓ Envoyé</span>')
    status_badge.short_description = "Statut"
    
    def to_emails_short(self, obj):
        emails = obj.to_emails[:50]
        if len(obj.to_emails) > 50:
            emails += "..."
        return emails
    to_emails_short.short_description = "Destinataires"
    
    def compose_link(self, obj):
        return format_html(
            '<a href="/tus-gestion-secure/emails/compose/" class="button" style="background: #0B2DFF; color: white; padding: 4px 12px; border-radius: 4px; text-decoration: none;">✉️ Nouveau</a>'
        )
    compose_link.short_description = "Action"
    
    fieldsets = (
        ('Destinataires', {
            'fields': ('to_emails', 'cc_emails', 'bcc_emails')
        }),
        ('Contenu', {
            'fields': ('subject', 'body_html', 'template_used')
        }),
        ('Métadonnées', {
            'fields': ('created_by', 'created_at', 'sent_at', 'is_draft'),
            'classes': ('collapse',)
        }),
    )
