"""URL patterns pour l'outil de diagnostic interne."""
from django.urls import path
from . import views

app_name = "diagnostic"

urlpatterns = [
    path("", views.diagnostic_list, name="diagnostic_list"),
    path("nouveau/", views.diagnostic_new, name="diagnostic_new"),
    path("<int:pk>/", views.diagnostic_detail, name="diagnostic_detail"),
    path("<int:pk>/relancer/", views.diagnostic_rerun, name="diagnostic_rerun"),
    path("<int:pk>/json/", views.diagnostic_api_json, name="diagnostic_json"),
]
