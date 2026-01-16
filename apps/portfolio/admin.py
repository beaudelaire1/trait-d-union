"""Admin pour le portfolio."""
from django.contrib import admin
from .models import Project, ProjectImage


class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 1


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'project_type', 'client_name', 'is_featured', 'is_published', 'created_at')
    list_filter = ('project_type', 'is_featured', 'is_published')
    search_fields = ('title', 'client_name', 'objective')
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ('is_featured', 'is_published')
    ordering = ('-created_at',)
    inlines = [ProjectImageInline]
    
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'project_type', 'client_name')
        }),
        ('Contenu', {
            'fields': ('objective', 'solution', 'result', 'technologies')
        }),
        ('Médias', {
            'fields': ('thumbnail', 'url')
        }),
        ('Options', {
            'fields': ('is_featured', 'is_published')
        }),
    )


@admin.register(ProjectImage)
class ProjectImageAdmin(admin.ModelAdmin):
    list_display = ('project', 'caption', 'order')
    list_filter = ('project',)
    ordering = ('project', 'order')
