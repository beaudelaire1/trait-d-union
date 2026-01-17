"""Admin configuration for client portal."""
from django.contrib import admin
from .models import (
    ClientProfile, Project, ProjectMilestone, ClientDocument,
    ProjectActivity, ProjectComment, ClientNotification
)


@admin.register(ClientProfile)
class ClientProfileAdmin(admin.ModelAdmin):
    """Admin for client profiles."""
    list_display = ['user', 'company_name', 'phone', 'created_at']
    search_fields = ['user__email', 'user__username', 'company_name', 'phone']
    list_filter = ['email_notifications', 'created_at']
    readonly_fields = ['created_at', 'updated_at']


class ProjectMilestoneInline(admin.TabularInline):
    """Inline for project milestones."""
    model = ProjectMilestone
    extra = 1
    ordering = ['order']


class ClientDocumentInline(admin.TabularInline):
    """Inline for project documents."""
    model = ClientDocument
    extra = 0
    fields = ['title', 'document_type', 'file', 'uploaded_by_client']


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
    """Admin for projects."""
    list_display = ['name', 'client', 'status', 'progress', 'start_date', 'estimated_delivery']
    list_filter = ['status', 'start_date', 'created_at']
    search_fields = ['name', 'client__company_name', 'client__user__email']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ProjectMilestoneInline, ProjectActivityInline, ProjectCommentInline, ClientDocumentInline]
    
    fieldsets = (
        (None, {
            'fields': ('client', 'name', 'description', 'quote')
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
    
    def save_model(self, request, obj, form, change):
        """Log activity when status or progress changes."""
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
        super().save_model(request, obj, form, change)


@admin.register(ProjectMilestone)
class ProjectMilestoneAdmin(admin.ModelAdmin):
    """Admin for milestones."""
    list_display = ['title', 'project', 'status', 'due_date', 'order']
    list_filter = ['status', 'due_date']
    search_fields = ['title', 'project__name']
    ordering = ['project', 'order']
    
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
    """Admin for client documents."""
    list_display = ['title', 'client', 'project', 'document_type', 'uploaded_by_client', 'created_at']
    list_filter = ['document_type', 'uploaded_by_client', 'created_at']
    search_fields = ['title', 'client__company_name', 'project__name']
    readonly_fields = ['created_at']


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
