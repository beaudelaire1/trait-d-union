"""Admin pour l'app diagnostic."""
from django.contrib import admin, messages
from django.shortcuts import redirect
from django.urls import reverse

from .models import SiteDiagnostic, FieldDiagnostic


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


@admin.register(FieldDiagnostic)
class FieldDiagnosticAdmin(admin.ModelAdmin):
    list_display = ["company_name", "profile", "overall_score", "created_at", "created_by"]
    list_filter = ["profile", "sector", "created_at"]
    search_fields = ["company_name", "contact_name", "contact_email"]
    readonly_fields = [
        "created_at", "updated_at", "created_by",
        "overall_score", "answers", "results",
    ]
    actions = ["send_report_email"]

    def has_add_permission(self, request):
        # Le bouton « Ajouter » reste visible, mais la création passe par
        # l'outil d'entretien dédié (questionnaire adapté au profil/secteur).
        return True

    def add_view(self, request, form_url="", extra_context=None):
        # Redirige le bouton natif « + Ajouter » vers le questionnaire terrain
        # plutôt que vers un formulaire admin brut (qui produirait une fiche
        # incohérente : score à 0, réponses non structurées).
        return redirect(reverse("diagnostic:field_new"))

    @admin.action(description="Envoyer le rapport par email au client")
    def send_report_email(self, request, queryset):
        from .views import send_field_report

        sent = 0
        for diag in queryset:
            ok, detail = send_field_report(diag, actor=request.user)
            if ok:
                sent += 1
            else:
                self.message_user(request, detail, level=messages.WARNING)
        if sent:
            self.message_user(
                request,
                f"{sent} rapport(s) envoyé(s) au client.",
                level=messages.SUCCESS,
            )
