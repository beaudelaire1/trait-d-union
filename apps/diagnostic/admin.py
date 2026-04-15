"""Admin pour l'app diagnostic."""
from django.contrib import admin
from .models import SiteDiagnostic


@admin.register(SiteDiagnostic)
class SiteDiagnosticAdmin(admin.ModelAdmin):
    list_display = ["url", "overall_score", "status", "created_at", "created_by"]
    list_filter = ["status", "created_at"]
    search_fields = ["url"]
    readonly_fields = [
        "url", "created_at", "created_by", "status",
        "overall_score", "results", "duration_seconds", "error_message",
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
