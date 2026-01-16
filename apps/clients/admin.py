"""Admin configuration for client portal."""
from django.contrib import admin
from .models import ClientProfile, Project, ProjectMilestone, ClientDocument


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


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Admin for projects."""
    list_display = ['name', 'client', 'status', 'progress', 'start_date', 'estimated_delivery']
    list_filter = ['status', 'start_date', 'created_at']
    search_fields = ['name', 'client__company_name', 'client__user__email']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [ProjectMilestoneInline, ClientDocumentInline]
    
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


@admin.register(ProjectMilestone)
class ProjectMilestoneAdmin(admin.ModelAdmin):
    """Admin for milestones."""
    list_display = ['title', 'project', 'status', 'due_date', 'order']
    list_filter = ['status', 'due_date']
    search_fields = ['title', 'project__name']
    ordering = ['project', 'order']


@admin.register(ClientDocument)
class ClientDocumentAdmin(admin.ModelAdmin):
    """Admin for client documents."""
    list_display = ['title', 'client', 'project', 'document_type', 'uploaded_by_client', 'created_at']
    list_filter = ['document_type', 'uploaded_by_client', 'created_at']
    search_fields = ['title', 'client__company_name', 'project__name']
    readonly_fields = ['created_at']
