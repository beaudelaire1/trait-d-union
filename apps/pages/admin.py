"""Admin configuration for the pages app."""
from django.contrib import admin
from django.utils.html import format_html

from .models import Testimonial


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    """Admin interface for testimonials (manual + Google sync)."""

    list_display = (
        "client_name", "company_name", "source_badge",
        "rating", "is_published", "order", "review_published_at", "last_synced_at",
    )
    list_filter = ("source", "is_published", "rating", "created_at")
    search_fields = ("client_name", "company_name", "content", "google_review_id")
    list_editable = ("is_published", "order")
    date_hierarchy = "created_at"
    readonly_fields = (
        "google_review_id", "review_url", "review_published_at",
        "last_synced_at", "created_at",
    )

    fieldsets = (
        ("Informations client", {
            "fields": ("client_name", "company_name", "position", "avatar", "avatar_url"),
        }),
        ("Témoignage", {
            "fields": ("content", "rating"),
        }),
        ("Provenance", {
            "fields": ("source", "google_review_id", "review_url", "review_published_at"),
            "description": (
                "Pour les avis synchronisés depuis Google, ces champs sont remplis "
                "automatiquement par <code>manage.py sync_google_reviews</code>."
            ),
        }),
        ("Publication", {
            "fields": ("is_published", "order", "last_synced_at", "created_at"),
        }),
    )

    @admin.display(description="Source", ordering="source")
    def source_badge(self, obj: Testimonial) -> str:
        if obj.source == "google":
            color = "#0F9D58"
            label = "Google"
        else:
            color = "#6B8AFF"
            label = "Manuel"
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:10px;font-size:0.75rem;">{}</span>',
            color, label,
        )
