"""Admin pour les leads."""
from django.contrib import admin, messages
from django.urls import reverse
from django.utils.html import format_html
from django.utils import timezone
from .models import Lead, LeadStatus
from .email_models import EmailTemplate, EmailComposition


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'email', 'project_type', 'budget',
        'status', 'client_link', 'attachment_link', 'created_at',
    )
    list_filter = ('status', 'project_type', 'budget', 'created_at', ('attachment', admin.EmptyFieldListFilter))
    search_fields = ('name', 'email', 'message', 'notes')
    readonly_fields = ('created_at', 'converted_to_client', 'converted_at')
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    list_editable = ('status',)
    actions = ['action_convert_to_client', 'action_mark_contacted', 'action_mark_lost']

    def attachment_link(self, obj):
        if obj.attachment:
            return format_html('<a href="{}" target="_blank" class="button">Télécharger</a>', obj.attachment.url)
        return "-"
    attachment_link.short_description = "Pièce jointe"

    def status_badge(self, obj):
        colors = {
            'new': '#3B82F6',
            'contacted': '#F59E0B',
            'qualified': '#10B981',
            'converted': '#22C55E',
            'lost': '#EF4444',
        }
        color = colors.get(obj.status, '#6B7280')
        return format_html(
            '<span style="background:{}; color:white; padding:3px 10px; '
            'border-radius:12px; font-size:11px; font-weight:600;">{}</span>',
            color, obj.get_status_display(),
        )
    status_badge.short_description = "Statut"

    def client_link(self, obj):
        if obj.converted_to_client:
            url = reverse('admin:clients_clientprofile_change', args=[obj.converted_to_client.pk])
            return format_html(
                '<a href="{}" style="color:#22C55E; font-weight:600;">👤 {}</a>',
                url, obj.converted_to_client.user.get_full_name() or obj.converted_to_client.user.email,
            )
        return "-"
    client_link.short_description = "Client"

    fieldsets = (
        ('Contact', {
            'fields': ('name', 'email')
        }),
        ('Projet', {
            'fields': ('project_type', 'budget', 'message', 'existing_url', 'attachment')
        }),
        ('Pipeline', {
            'fields': ('status', 'notes'),
        }),
        ('Conversion', {
            'fields': ('converted_to_client', 'converted_at'),
            'classes': ('collapse',),
            'description': 'Informations sur la conversion en client (renseigné automatiquement).',
        }),
        ('Métadonnées', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )

    # ------------------------------------------------------------------ actions

    @admin.action(description="🎉 Convertir en client (créer compte portail)")
    def action_convert_to_client(self, request, queryset):
        """Convertit les leads sélectionnés en comptes client.

        Crée un User + ClientProfile avec mot de passe temporaire
        et envoie l'email de bienvenue automatiquement.
        """
        from apps.clients.services import create_client_account, ClientAccountError

        converted = 0
        skipped = 0
        errors = []

        for lead in queryset:
            # Déjà converti ?
            if lead.is_converted:
                skipped += 1
                continue

            try:
                result = create_client_account(
                    email=lead.email,
                    full_name=lead.name,
                    send_email=True,
                )

                lead.converted_to_client = result.client_profile
                lead.converted_at = timezone.now()
                lead.status = LeadStatus.CONVERTED
                lead.is_processed = True
                lead.save(update_fields=[
                    'converted_to_client', 'converted_at', 'status', 'is_processed',
                ])
                converted += 1
            except ClientAccountError as e:
                errors.append(f"{lead.name} : {e}")
            except Exception as e:
                errors.append(f"{lead.name} : {e}")

        # Messages
        if converted:
            self.message_user(
                request,
                f"✅ {converted} lead(s) converti(s) en client. "
                f"Email de bienvenue envoyé avec identifiants.",
                level=messages.SUCCESS,
            )
        if skipped:
            self.message_user(
                request,
                f"⏭️ {skipped} lead(s) déjà converti(s), ignoré(s).",
                level=messages.WARNING,
            )
        if errors:
            self.message_user(
                request,
                f"❌ Erreurs : {' | '.join(errors)}",
                level=messages.ERROR,
            )

    @admin.action(description="📧 Marquer comme contacté")
    def action_mark_contacted(self, request, queryset):
        updated = queryset.exclude(status=LeadStatus.CONVERTED).update(status=LeadStatus.CONTACTED)
        self.message_user(request, f"{updated} lead(s) marqué(s) comme contacté(s).", level=messages.SUCCESS)

    @admin.action(description="❌ Marquer comme perdu")
    def action_mark_lost(self, request, queryset):
        updated = queryset.exclude(status=LeadStatus.CONVERTED).update(status=LeadStatus.LOST)
        self.message_user(request, f"{updated} lead(s) marqué(s) comme perdu(s).", level=messages.SUCCESS)


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
