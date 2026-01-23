"""Admin configuration for the pages app."""
from django.contrib import admin

from .models import Testimonial


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
