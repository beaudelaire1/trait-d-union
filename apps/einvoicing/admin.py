"""Admin (lecture seule) pour le journal de cycle de vie des factures."""

from __future__ import annotations

from django.contrib import admin
from django.utils.html import format_html

from .models import InvoiceLifecycleEvent


@admin.register(InvoiceLifecycleEvent)
class InvoiceLifecycleEventAdmin(admin.ModelAdmin):
    """Lecture seule absolue : aucune écriture possible depuis l'admin.

    Cohérent avec le caractère append-only du modèle.
    """

    list_display = (
        "id",
        "invoice_link",
        "state",
        "occurred_at",
        "source",
        "actor",
        "short_hash",
    )
    list_filter = ("state", "source", "occurred_at")
    search_fields = (
        "invoice__number",
        "invoice__id",
        "event_hash",
        "previous_hash",
        "source",
    )
    date_hierarchy = "occurred_at"
    readonly_fields = (
        "invoice",
        "state",
        "occurred_at",
        "actor",
        "source",
        "payload",
        "previous_hash",
        "event_hash",
    )
    ordering = ("-occurred_at", "-id")

    # ─── Strict read-only ────────────────────────────────────────────
    def has_add_permission(self, request):  # pragma: no cover
        return False

    def has_change_permission(self, request, obj=None):  # pragma: no cover
        return False

    def has_delete_permission(self, request, obj=None):  # pragma: no cover
        return False

    # ─── Display helpers ─────────────────────────────────────────────
    @admin.display(description="Facture", ordering="invoice__number")
    def invoice_link(self, obj: InvoiceLifecycleEvent) -> str:
        if obj.invoice_id and obj.invoice:
            return format_html("<code>{}</code>", obj.invoice.number or obj.invoice_id)
        return "—"

    @admin.display(description="Hash")
    def short_hash(self, obj: InvoiceLifecycleEvent) -> str:
        return format_html("<code title='{}'>{}…</code>", obj.event_hash, (obj.event_hash or "")[:10])
