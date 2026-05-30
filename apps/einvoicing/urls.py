"""URLs internes de l'app einvoicing — webhooks PDP entrants."""

from __future__ import annotations

from django.urls import path

from .views_webhooks import b2brouter_webhook, iopole_webhook


app_name = "einvoicing"

urlpatterns = [
    path("webhooks/b2brouter/", b2brouter_webhook, name="webhook_b2brouter"),
    path("webhooks/iopole/", iopole_webhook, name="webhook_iopole"),
]
