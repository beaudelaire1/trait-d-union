"""URL patterns pour l'outil de diagnostic interne (numérique + terrain)."""
from django.urls import path
from . import views

app_name = "diagnostic"

urlpatterns = [
    # Page de choix Numérique / Terrain
    path("", views.diagnostic_home, name="diagnostic_home"),

    # ── Diagnostic numérique (analyse d'URL) ────────────────────────
    path("numerique/", views.diagnostic_list, name="diagnostic_list"),
    path("numerique/nouveau/", views.diagnostic_new, name="diagnostic_new"),
    path("numerique/<int:pk>/", views.diagnostic_detail, name="diagnostic_detail"),
    path("numerique/<int:pk>/relancer/", views.diagnostic_rerun, name="diagnostic_rerun"),
    path("numerique/<int:pk>/json/", views.diagnostic_api_json, name="diagnostic_json"),

    # ── Diagnostic terrain (entretien structuré) ────────────────────
    path("terrain/", views.field_list, name="field_list"),
    path("terrain/nouveau/", views.field_new, name="field_new"),
    path("terrain/<int:pk>/questionnaire/", views.field_form, name="field_form"),
    path("terrain/<int:pk>/", views.field_detail, name="field_detail"),
    path("terrain/<int:pk>/pdf/", views.field_pdf, name="field_pdf"),
    path("terrain/<int:pk>/envoyer/", views.field_send_email, name="field_send_email"),
    path("terrain/<int:pk>/supprimer/", views.field_delete, name="field_delete"),
]

