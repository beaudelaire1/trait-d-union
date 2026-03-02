"""Admin configuration for client portal."""
from django.contrib import admin, messages
from django.utils.html import format_html
from django import forms
from django.contrib.auth.models import User
from .models import (
    ClientProfile, Project, ProjectMilestone, ClientDocument,
    ProjectActivity, ProjectComment, ClientNotification,
    WorkflowTemplate, MilestoneTemplate
)


class ClientProfileCreationForm(forms.ModelForm):
    """Formulaire de création rapide d'un compte client portail.
    
    Permet de créer User + ClientProfile en une seule étape
    depuis l'admin, sans passer par un devis.
    """
    email = forms.EmailField(
        label="Email du client",
        help_text="Un compte utilisateur sera créé automatiquement avec cet email."
    )
    full_name = forms.CharField(
        label="Nom complet",
        max_length=200,
        required=False,
        help_text="Prénom Nom du client."
    )
    send_welcome_email = forms.BooleanField(
        label="Envoyer l'email de bienvenue",
        initial=True,
        required=False,
        help_text="Coche pour envoyer automatiquement les identifiants par email."
    )

    class Meta:
        model = ClientProfile
        fields = ['email', 'full_name', 'company_name', 'phone', 'address_line', 'city', 'zip_code', 'address', 'send_welcome_email']

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        # Vérifie si un profil client existe déjà pour cet email
        existing_user = User.objects.filter(email__iexact=email).first()
        if existing_user and hasattr(existing_user, 'client_profile'):
            raise forms.ValidationError(
                f"Un compte client existe déjà pour {email}."
            )
        return email

    def save(self, commit=True):
        from .services import create_client_account
        email = self.cleaned_data['email']
        result = create_client_account(
            email=email,
            full_name=self.cleaned_data.get('full_name', ''),
            company_name=self.cleaned_data.get('company_name', ''),
            phone=self.cleaned_data.get('phone', ''),
            address=self.cleaned_data.get('address', ''),
            send_email=self.cleaned_data.get('send_welcome_email', True),
        )
        # Stocker le résultat pour le message admin
        self._account_result = result
        return result.client_profile


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    """Admin for client profiles — création rapide et gestion complète."""
    list_display = ['full_name', 'email', 'company_name', 'phone', 'portal_status_badge', 'created_at']
    search_fields = ['full_name', 'email', 'company_name', 'phone', 'user__username']
    list_filter = ['email_notifications', 'must_change_password', 'created_at']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['action_reset_password', 'action_resend_welcome_email']

    def get_form(self, request, obj=None, **kwargs):
        """Utilise le formulaire de création rapide pour les nouveaux profils."""
        if obj is None:  # Création
            kwargs['form'] = ClientProfileCreationForm
        return super().get_form(request, obj, **kwargs)

    def get_fieldsets(self, request, obj=None):
        """Fieldsets adaptés : création vs modification."""
        if obj is None:  # Création
            return (
                ('Nouveau compte client', {
                    'fields': ('email', 'full_name', 'company_name', 'phone', 'address_line', 'city', 'zip_code', 'address', 'send_welcome_email'),
                    'description': (
                        '🆕 <strong>Création rapide :</strong> '
                        'Renseignez l\'email du client. Un compte utilisateur sera créé '
                        'automatiquement avec un mot de passe temporaire. '
                        'Le client devra le changer à sa première connexion.'
                    )
                }),
            )
        # Modification
        return (
            ('Identité', {
                'fields': ('full_name', 'email', 'company_name', 'phone')
            }),
            ('Adresse', {
                'fields': ('address_line', 'city', 'zip_code', 'address')
            }),
            ('Portail', {
                'fields': ('user', 'siret', 'tva_number', 'avatar')
            }),
            ('Préférences', {
                'fields': ('email_notifications', 'must_change_password')
            }),
            ('Métadonnées', {
                'fields': ('created_at', 'updated_at'),
                'classes': ('collapse',)
            }),
        )

    def save_model(self, request, obj, form, change):
        """Message de confirmation après création."""
        if not change and isinstance(form, ClientProfileCreationForm):
            # La sauvegarde est gérée par le formulaire
            result = form._account_result
            if result.is_new:
                messages.success(
                    request,
                    f"✅ Compte client créé : {result.user.email} — "
                    f"Mot de passe temporaire envoyé par email."
                )
            else:
                messages.info(
                    request,
                    f"ℹ️ Compte existant récupéré : {result.user.email}"
                )
        else:
            super().save_model(request, obj, form, change)

    def portal_status_badge(self, obj):
        """Badge indiquant l'état du compte portail."""
        if not obj.user_id:
            return format_html(
                '<span style="background:rgba(107,114,128,0.15); color:#9CA3AF; '
                'padding:3px 10px; border-radius:12px; font-size:0.75rem; '
                'font-weight:600;">📇 Contact</span>'
            )
        if obj.must_change_password:
            return format_html(
                '<span style="background:rgba(245,158,11,0.15); color:#FCD34D; '
                'padding:3px 10px; border-radius:12px; font-size:0.75rem; '
                'font-weight:600;">⏳ Mot de passe à changer</span>'
            )
        if obj.user.last_login:
            return format_html(
                '<span style="background:rgba(34,197,94,0.15); color:#4ADE80; '
                'padding:3px 10px; border-radius:12px; font-size:0.75rem; '
                'font-weight:600;">✅ Actif</span>'
            )
        return format_html(
            '<span style="background:rgba(107,114,128,0.15); color:#9CA3AF; '
            'padding:3px 10px; border-radius:12px; font-size:0.75rem; '
            'font-weight:600;">🔒 Jamais connecté</span>'
        )
    portal_status_badge.short_description = "Portail"

    @admin.action(description="🔑 Réinitialiser le mot de passe et notifier")
    def action_reset_password(self, request, queryset):
        """Réinitialise le mot de passe et envoie un email (async)."""
        from core.tasks import async_reset_password_notify
        count = 0
        for profile in queryset:
            try:
                async_reset_password_notify(profile.user.pk)
                count += 1
            except Exception as e:
                messages.error(request, f"Erreur pour {profile.user.email}: {e}")
        if count:
            messages.success(
                request,
                f"🔑 {count} mot(s) de passe réinitialisé(s). Email(s) en cours d'envoi."
            )

    @admin.action(description="📧 Renvoyer l'email de bienvenue (nouveau mot de passe)")
    def action_resend_welcome_email(self, request, queryset):
        """Renvoie l'email de bienvenue avec un nouveau mot de passe (async)."""
        from core.tasks import async_reset_password_notify
        count = 0
        for profile in queryset:
            try:
                async_reset_password_notify(profile.user.pk)
                count += 1
            except Exception as e:
                messages.error(request, f"Erreur pour {profile.user.email}: {e}")
        if count:
            messages.success(
                request,
                f"📧 {count} email(s) de bienvenue en cours d'envoi."
            )


class ProjectMilestoneInline(admin.StackedInline):
    """Inline for project milestones — format empilé avec checklist visible."""
    model = ProjectMilestone
    extra = 0
    ordering = ['order']
    fields = [
        ('order', 'title', 'status'),
        'description',
        ('due_date', 'responsible'),
        'checklist',
        ('validation_comment',),
    ]
    readonly_fields = ['completed_at', 'validated_at', 'validated_by']
    
    class Media:
        css = {
            'all': ['admin/css/forms.css']
        }


class ClientDocumentInline(admin.StackedInline):
    """Inline for project documents — format empilé pour plus de lisibilité."""
    model = ClientDocument
    extra = 0
    fields = ['title', 'document_type', 'file', 'notes', 'uploaded_by_client']
    classes = ['collapse']


class ProjectActivityInline(admin.TabularInline):
    """Inline for project activities."""
    model = ProjectActivity
    extra = 0
    readonly_fields = ['created_at']
    fields = ['activity_type', 'title', 'description', 'performed_by', 'is_client_visible', 'created_at']
    ordering = ['-created_at']


class ProjectCommentInline(admin.TabularInline):
    """Inline for project comments."""
    model = ProjectComment
    extra = 0
    readonly_fields = ['created_at']
    fields = ['author', 'message', 'is_internal', 'created_at']
    ordering = ['-created_at']


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Admin for projects.
    
    TUS FLOW UPGRADE V2 : Intégration workflow template
    - Sélectionner un workflow → jalons générés automatiquement
    - OU ajouter des jalons manuellement via l'inline
    """
    list_display = ['name', 'client', 'status', 'progress', 'start_date', 'estimated_delivery', 'workflow_used']
    list_filter = ['status', 'workflow_template', 'start_date', 'created_at']
    search_fields = ['name', 'client__company_name', 'client__user__email']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ProjectMilestoneInline, ProjectActivityInline, ProjectCommentInline, ClientDocumentInline]
    
    fieldsets = (
        (None, {
            'fields': ('client', 'name', 'description', 'quote')
        }),
        ('Workflow & Jalons', {
            'fields': ('workflow_template',),
            'description': (
                '💡 <strong>Conseil :</strong> Sélectionnez un workflow pour générer automatiquement les jalons.<br>'
                'Les jalons seront créés lors de la sauvegarde si aucun jalon n\'existe déjà.<br>'
                'Vous pouvez aussi ajouter des jalons manuellement ci-dessous.'
            )
        }),
        ('Statut', {
            'fields': ('status', 'progress')
        }),
        ('Dates', {
            'fields': ('start_date', 'estimated_delivery', 'delivered_at')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def workflow_used(self, obj):
        """Affiche le workflow utilisé."""
        if obj.workflow_template:
            return f"✅ {obj.workflow_template.name}"
        return "❌ Manuel"
    workflow_used.short_description = "Workflow"
    
    def save_model(self, request, obj, form, change):
        """Log activity when status or progress changes.
        
        TUS FLOW UPGRADE V2 : Auto-génération des jalons si workflow_template sélectionné
        """
        # Sauvegarder d'abord le projet pour obtenir un ID
        is_new = not change
        super().save_model(request, obj, form, change)
        
        # Si nouveau projet ET workflow_template sélectionné ET aucun jalon existant
        if is_new and obj.workflow_template and obj.milestones.count() == 0:
            # Générer automatiquement les jalons depuis le template
            milestones = obj.generate_milestones_from_template()
            
            # Message de succès
            self.message_user(
                request,
                f"✅ {len(milestones)} jalons générés automatiquement depuis le workflow '{obj.workflow_template.name}'",
                level='success'
            )
            
            # Log de l'activité
            ProjectActivity.objects.create(
                project=obj,
                activity_type='milestone_created',
                title=f"Jalons générés automatiquement",
                description=f"{len(milestones)} jalons créés depuis le workflow '{obj.workflow_template.name}'",
                performed_by=request.user,
                is_client_visible=False
            )
        
        # Log des changements de statut/progression (code existant)
        if change:
            old_obj = Project.objects.get(pk=obj.pk)
            # Log status change
            if old_obj.status != obj.status:
                ProjectActivity.objects.create(
                    project=obj,
                    activity_type='status_change',
                    title=f"Statut → {obj.get_status_display()}",
                    description=f"Le projet passe de {old_obj.get_status_display()} à {obj.get_status_display()}",
                    performed_by=request.user,
                    is_client_visible=True
                )
            # Log progress change
            if old_obj.progress != obj.progress:
                ProjectActivity.objects.create(
                    project=obj,
                    activity_type='progress_update',
                    title=f"Progression → {obj.progress}%",
                    description=f"La progression passe de {old_obj.progress}% à {obj.progress}%",
                    performed_by=request.user,
                    is_client_visible=True
                )
    
    # ============================================================
    # TUS FLOW UPGRADE V2 : Actions Admin
    # ============================================================
    
    actions = ['generate_milestones_action', 'regenerate_milestones_action']
    
    def generate_milestones_action(self, request, queryset):
        """Action : Générer les jalons depuis le workflow template."""
        count_success = 0
        count_skip = 0
        
        for project in queryset:
            if not project.workflow_template:
                count_skip += 1
                continue
            
            if project.milestones.count() > 0:
                count_skip += 1
                continue
            
            # Générer les jalons
            milestones = project.generate_milestones_from_template()
            count_success += 1
            
            # Log
            ProjectActivity.objects.create(
                project=project,
                activity_type='milestone_created',
                title=f"Jalons générés par action admin",
                description=f"{len(milestones)} jalons créés depuis '{project.workflow_template.name}'",
                performed_by=request.user,
                is_client_visible=False
            )
        
        if count_success > 0:
            self.message_user(
                request,
                f"✅ {count_success} projet(s) : jalons générés avec succès",
                level='success'
            )
        if count_skip > 0:
            self.message_user(
                request,
                f"⚠️ {count_skip} projet(s) ignorés (pas de workflow ou jalons existants)",
                level='warning'
            )
    
    generate_milestones_action.short_description = "🎯 Générer les jalons depuis workflow"
    
    def regenerate_milestones_action(self, request, queryset):
        """Action : Régénérer les jalons (supprime et recrée)."""
        count = 0
        
        for project in queryset:
            if not project.workflow_template:
                continue
            
            # Supprimer les jalons existants
            deleted_count = project.milestones.count()
            project.reset_milestones()
            
            # Régénérer
            milestones = project.generate_milestones_from_template()
            count += 1
            
            # Log
            ProjectActivity.objects.create(
                project=project,
                activity_type='milestone_created',
                title=f"Jalons régénérés",
                description=f"{deleted_count} jalons supprimés, {len(milestones)} jalons créés depuis '{project.workflow_template.name}'",
                performed_by=request.user,
                is_client_visible=False
            )
        
        self.message_user(
            request,
            f"✅ {count} projet(s) : jalons régénérés avec succès",
            level='success'
        )
    
    regenerate_milestones_action.short_description = "🔄 Régénérer les jalons (⚠️ supprime les existants)"


@admin.register(ProjectMilestone)
class ProjectMilestoneAdmin(admin.ModelAdmin):
    """Admin for milestones — avec validation rapide et badge statut."""
    list_display = ['title', 'project', 'status', 'status_badge', 'due_date', 'order', 'responsible']
    list_filter = ['status', 'due_date', 'project']
    search_fields = ['title', 'project__name']
    ordering = ['project', 'order']
    list_editable = ['status', 'order']
    autocomplete_fields = ['project', 'responsible']
    
    fieldsets = (
        (None, {
            'fields': ('project', 'title', 'description', 'order')
        }),
        ('Statut & Dates', {
            'fields': ('status', 'due_date', 'responsible')
        }),
        ('Checklist', {
            'fields': ('checklist',),
            'description': 'Format JSON : [{"id": 1, "text": "Tâche", "checked": false}]'
        }),
        ('Validation', {
            'fields': ('validation_comment', 'validated_by', 'validated_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    readonly_fields = ['validated_by', 'validated_at', 'completed_at']
    
    actions = ['mark_completed_action', 'mark_in_progress_action']
    
    def status_badge(self, obj):
        """Badge coloré pour le statut."""
        colors = {
            'pending': '#6B7280',
            'in_progress': '#0B2DFF',
            'completed': '#22C55E',
        }
        labels = {
            'pending': '⏳ En attente',
            'in_progress': '🔄 En cours',
            'completed': '✅ Terminé',
        }
        color = colors.get(obj.status, '#6B7280')
        label = labels.get(obj.status, obj.status)
        return format_html(
            '<span style="background:{}; color:white; padding:2px 8px; '
            'border-radius:4px; font-size:0.75rem; font-weight:600;">{}</span>',
            color, label
        )
    status_badge.short_description = "Statut"
    
    @admin.action(description="✅ Marquer comme terminé")
    def mark_completed_action(self, request, queryset):
        count = 0
        for milestone in queryset:
            if milestone.status != 'completed':
                milestone.mark_completed()
                count += 1
                ProjectActivity.objects.create(
                    project=milestone.project,
                    activity_type='milestone_completed',
                    title=f"Jalon terminé : {milestone.title}",
                    description=milestone.description or "",
                    performed_by=request.user,
                    milestone=milestone,
                    is_client_visible=True
                )
        self.message_user(request, f"✅ {count} jalon(s) marqué(s) comme terminé(s).")
    
    @admin.action(description="🔄 Marquer en cours")
    def mark_in_progress_action(self, request, queryset):
        count = queryset.filter(status='pending').update(status='in_progress')
        self.message_user(request, f"🔄 {count} jalon(s) marqué(s) en cours.")
    
    def save_model(self, request, obj, form, change):
        """Log activity when milestone is completed."""
        if change:
            old_obj = ProjectMilestone.objects.get(pk=obj.pk)
            if old_obj.status != 'completed' and obj.status == 'completed':
                ProjectActivity.objects.create(
                    project=obj.project,
                    activity_type='milestone_completed',
                    title=f"Jalon terminé : {obj.title}",
                    description=obj.description or "",
                    performed_by=request.user,
                    milestone=obj,
                    is_client_visible=True
                )
        super().save_model(request, obj, form, change)


@admin.register(ClientDocument)
class ClientDocumentAdmin(admin.ModelAdmin):
    """Admin for client documents — dépôt facile de devis/factures/documents."""
    list_display = ['title', 'client', 'project', 'document_type_badge', 'uploaded_by_client', 'created_at']
    list_filter = ['document_type', 'uploaded_by_client', 'created_at']
    search_fields = ['title', 'client__company_name', 'client__user__email', 'project__name']
    readonly_fields = ['created_at']
    autocomplete_fields = ['client', 'project']
    
    fieldsets = (
        ('Document', {
            'fields': ('title', 'document_type', 'file', 'notes'),
            'description': '💡 Utilisez les types <strong>Devis</strong> ou <strong>Facture</strong> '
                           'pour un classement automatique côté portail client.'
        }),
        ('Destinataire', {
            'fields': ('client', 'project'),
            'description': 'Sélectionnez le client et optionnellement le projet associé.'
        }),
        ('Métadonnées', {
            'fields': ('uploaded_by_client', 'created_at'),
            'classes': ('collapse',)
        }),
    )
    
    def document_type_badge(self, obj):
        """Affiche le type de document avec un badge coloré."""
        colors = {
            'devis': '#0B2DFF',
            'facture': '#22C55E',
            'contract': '#F59E0B',
            'brief': '#8B5CF6',
            'logo': '#EC4899',
            'asset': '#06B6D4',
            'other': '#6B7280',
        }
        color = colors.get(obj.document_type, '#6B7280')
        label = obj.get_document_type_display()
        return format_html(
            '<span style="background:{}; color:white; padding:2px 8px; '
            'border-radius:4px; font-size:0.75rem; font-weight:600;">{}</span>',
            color, label
        )
    document_type_badge.short_description = "Type"


@admin.register(ProjectActivity)
class ProjectActivityAdmin(admin.ModelAdmin):
    """Admin for project activities."""
    list_display = ['project', 'activity_type', 'title', 'performed_by', 'is_client_visible', 'created_at']
    list_filter = ['activity_type', 'is_client_visible', 'created_at']
    search_fields = ['title', 'description', 'project__name']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'


@admin.register(ProjectComment)
class ProjectCommentAdmin(admin.ModelAdmin):
    """Admin for project comments."""
    list_display = ['project', 'author', 'short_message', 'is_internal', 'read_by_client', 'created_at']
    list_filter = ['is_internal', 'read_by_client', 'created_at']
    search_fields = ['message', 'project__name', 'author__username']
    readonly_fields = ['created_at', 'updated_at']
    
    def short_message(self, obj):
        return obj.message[:50] + '...' if len(obj.message) > 50 else obj.message
    short_message.short_description = "Message"


@admin.register(ClientNotification)
class ClientNotificationAdmin(admin.ModelAdmin):
    """Admin for client notifications."""
    list_display = ['client', 'notification_type', 'title', 'read', 'created_at']
    list_filter = ['notification_type', 'read', 'created_at']
    search_fields = ['title', 'message', 'client__company_name']
    readonly_fields = ['created_at']


# ============================================================
# TUS FLOW UPGRADE : Workflow Templates Admin
# ============================================================

class MilestoneTemplateInline(admin.TabularInline):
    """Inline pour les templates de jalons dans un workflow."""
    model = MilestoneTemplate
    extra = 1
    ordering = ['order']
    fields = ['order', 'title', 'description', 'estimated_duration_days']
    
    class Media:
        css = {
            'all': ['admin/css/forms.css']
        }


@admin.register(WorkflowTemplate)
class WorkflowTemplateAdmin(admin.ModelAdmin):
    """Admin pour les templates de workflow réutilisables.
    
    Permet de créer des workflows types (Site Web, App Mobile, etc.)
    avec leurs jalons pré-configurés.
    """
    list_display = ['name', 'milestone_count', 'total_estimated_days', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    inlines = [MilestoneTemplateInline]
    
    fieldsets = (
        (None, {
            'fields': ('name', 'description', 'is_active')
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['duplicate_workflow']
    
    def milestone_count(self, obj):
        """Nombre de jalons dans ce workflow."""
        return obj.milestone_templates.count()
    milestone_count.short_description = "Nb jalons"
    
    def total_estimated_days(self, obj):
        """Durée totale estimée (uses annotated value to avoid N+1)."""
        total = getattr(obj, '_total_days', None)
        if total is None:
            total = sum(m.estimated_duration_days for m in obj.milestone_templates.all())
        return f"{total} jours"
    total_estimated_days.short_description = "Durée estimée"
    total_estimated_days.admin_order_field = '_total_days'

    def get_queryset(self, request):
        """⚡ PERFORMANCE: Annotate total days to avoid N+1 in list_display."""
        from django.db.models import Sum
        qs = super().get_queryset(request)
        return qs.annotate(
            _total_days=Sum('milestone_templates__estimated_duration_days')
        )
    
    def duplicate_workflow(self, request, queryset):
        """Action pour dupliquer un workflow."""
        for workflow in queryset:
            new_name = f"{workflow.name} (copie)"
            workflow.duplicate(new_name)
        self.message_user(request, f"{queryset.count()} workflow(s) dupliqué(s)")
    duplicate_workflow.short_description = "Dupliquer les workflows sélectionnés"


@admin.register(MilestoneTemplate)
class MilestoneTemplateAdmin(admin.ModelAdmin):
    """Admin pour les templates de jalons individuels."""
    list_display = ['workflow', 'order', 'title', 'estimated_duration_days']
    list_filter = ['workflow']
    search_fields = ['title', 'description']
    ordering = ['workflow', 'order']
    
    fieldsets = (
        (None, {
            'fields': ('workflow', 'title', 'description', 'order', 'estimated_duration_days')
        }),
        ('Checklist Template', {
            'fields': ('checklist_template',),
            'description': 'JSON format : [{"text": "Tâche 1"}, {"text": "Tâche 2"}]'
        }),
    )

