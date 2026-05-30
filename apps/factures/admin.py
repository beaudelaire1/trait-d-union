"""
Configuration de l'administration pour l'app ``factures``.

Cette configuration permet de générer des PDF pour les factures sélectionnées
directement depuis la liste dans l'admin et de visualiser les attributs
principaux (numéro, devis associé, montant, date).
"""

from django.contrib import admin, messages
from django.utils.html import format_html
from django.core.files.base import ContentFile
from django import forms
import os
from django.urls import reverse

from .models import Invoice, InvoiceItem
from .services import PremiumEmailService
from apps.clients.models import ClientDocument, ClientNotification


class InvoiceAdminForm(forms.ModelForm):
    """Custom admin form for Invoice with Textarea for notes field."""
    
    notes = forms.CharField(
        label="Notes",
        widget=forms.Textarea(attrs={'cols': 80, 'rows': 15}),
        required=False,
        help_text="Notes pour la facture"
    )
    
    class Meta:
        model = Invoice
        fields = '__all__'


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    form = InvoiceAdminForm
    list_display = ("number", "client_name", "status", "lifecycle_state", "issue_date", "total_ttc", "pdf_link")
    list_filter = ("status", "lifecycle_state", "transaction_type", "is_credit_note", "issue_date")
    search_fields = ("number", "client__full_name", "quote__client__full_name", "buyer_reference", "purchase_order_ref")
    autocomplete_fields = ("client",)
    raw_id_fields = ("quote", "credit_note_for")
    fieldsets = (
        (None, {
            "fields": ("quote", "client", "command_ref", "number", "issue_date", "due_date", "status"),
        }),
        ("E-invoicing FR (2026/2027)", {
            "fields": (
                "invoice_type_code",
                "transaction_type",
                "vat_payment_basis",
                ("delivery_date", "delivery_period_start", "delivery_period_end"),
                ("buyer_reference", "purchase_order_ref", "contract_ref"),
                "currency_code",
                "lifecycle_state",
                ("is_credit_note", "credit_note_for"),
            ),
            "description": (
                "Mentions obligatoires dès le 1er sept 2026 (réception) "
                "et 1er sept 2027 (émission TPE). Le SIREN du client est "
                "tiré automatiquement de sa fiche."
            ),
        }),
        ("Totaux", {
            "fields": ("total_ht", "tva", "total_ttc", "discount", "amount"),
        }),
        ("Notes & PDF", {
            "fields": ("notes", "payment_terms", "pdf"),
        }),
        ("Paiement & dunning", {
            "fields": (
                "stripe_checkout_session_id",
                ("amount_paid", "paid_at"),
                ("paid_by", "payment_proof"),
                "payment_audit_trail",
                ("last_reminder_level", "last_reminder_date", "reminder_count", "dunning_completed"),
            ),
            "classes": ("collapse",),
        }),
    )

    @admin.display(description="Client", ordering="client__full_name")
    def client_name(self, obj):
        if obj.client:
            return obj.client.full_name
        if obj.quote and obj.quote.client:
            return obj.quote.client.full_name
        return "—"
    readonly_fields = ("total_ht", "tva", "total_ttc", "issue_date", "created_at")
    actions = [
        "generate_pdfs",
        "generate_facturx_pdfs",
        "send_invoices",
        "generate_pdfs_and_publish",
        "send_invoices_and_publish",
    ]

    class InvoiceItemInline(admin.TabularInline):
        model = InvoiceItem
        extra = 1
        fields = (
            "description",
            "quantity",
            "unit_code",
            "unit_price",
            "vat_category_code",
            "vat_exemption_reason_code",
            "tax_rate",
            "line_discount",
            "total_ht",
            "total_tva",
            "total_ttc",
        )
        readonly_fields = ("total_ht", "total_tva", "total_ttc")

    inlines = [InvoiceItemInline]

    def save_formset(self, request, form, formset, change):
        instances = formset.save()
        if formset.model is InvoiceItem:
            form.instance.compute_totals()
        return instances

    def generate_pdfs(self, request, queryset):
        """Action admin pour générer les fichiers PDF des factures sélectionnées."""
        count = 0
        for invoice in queryset:
            # recalculer les totaux avant génération
            invoice.compute_totals()
            invoice.generate_pdf()
            invoice.save()
            count += 1
        self.message_user(request, f"{count} facture(s) convertie(s) en PDF.")
    generate_pdfs.short_description = "Générer les PDF pour les factures sélectionnées"

    @admin.action(description="🇫🇷 Générer en Factur-X (PDF/A-3 + XML CII, conforme EN 16931)")
    def generate_facturx_pdfs(self, request, queryset):
        """Action admin Phase 2 — produit un Factur-X (PDF/A-3 + XML CII embarqué).

        Le rendu visuel reste identique au PDF classique. Seule la "couche
        machine" est ajoutée (XML embarqué + métadonnées XMP PDF/A-3).
        """
        ok = 0
        ko = 0
        for invoice in queryset:
            try:
                invoice.compute_totals()
                invoice.generate_pdf(attach=True, format="facturx")
                invoice.save()
                ok += 1
            except Exception as exc:  # noqa: BLE001
                ko += 1
                self.message_user(
                    request,
                    f"Facture {invoice.number}: échec Factur-X — {exc}",
                    level=messages.ERROR,
                )
        if ok:
            self.message_user(
                request,
                f"✅ {ok} facture(s) convertie(s) en Factur-X (PDF/A-3 + XML CII).",
                level=messages.SUCCESS,
            )
        if ko:
            self.message_user(
                request,
                f"⚠️ {ko} facture(s) en échec — voir messages d'erreur.",
                level=messages.WARNING,
            )

    @admin.action(description="📄 Générer les PDF et publier sur portail")
    def generate_pdfs_and_publish(self, request, queryset):
        published = 0
        for invoice in queryset:
            invoice.compute_totals()
            invoice.generate_pdf(attach=True)
            invoice.save()
            if publish_invoice_to_portal(invoice, request):
                published += 1
        self.message_user(request, f"PDF générés. {published} publié(s) sur le portail.", level=messages.SUCCESS)

    def pdf_link(self, obj: Invoice) -> str:
        """Retourne un lien vers la vue download si un PDF existe."""
        if obj.pdf:
            url = reverse("factures:download", args=[obj.pk])
            return format_html("<a href='{}' target='_blank'>Ouvrir</a>", url)
        return "–"
    pdf_link.short_description = "PDF"

    def send_invoices(self, request, queryset):
        """Action admin pour envoyer les factures sélectionnées par e‑mail."""
        count = 0
        email_service = PremiumEmailService()
        for invoice in queryset:
            # Recalculer les totaux et générer un PDF à jour
            invoice.compute_totals()
            invoice.generate_pdf(attach=True)
            try:
                email_service.send_invoice_notification(invoice)
                count += 1
            except Exception:
                # En cas d'erreur d'envoi, on passe à la facture suivante
                continue
        self.message_user(request, f"{count} facture(s) envoyée(s) par e‑mail.")
    send_invoices.short_description = "Envoyer les factures sélectionnées par e‑mail"

    @admin.action(description="📧 Envoyer les factures et publier sur portail")
    def send_invoices_and_publish(self, request, queryset):
        published = 0
        email_service = PremiumEmailService()
        for invoice in queryset:
            invoice.compute_totals()
            invoice.generate_pdf(attach=True)
            try:
                email_service.send_invoice_notification(invoice)
                if publish_invoice_to_portal(invoice, request):
                    published += 1
            except Exception:
                continue
        self.message_user(request, f"Factures envoyées. {published} publié(s) sur le portail.", level=messages.SUCCESS)


def publish_invoice_to_portal(invoice: Invoice, request=None) -> bool:
    """Publie le PDF de facture dans le portail client (ClientDocument + notification)."""
    try:
        client = invoice.client
        if not client or not client.email:
            if request:
                messages.warning(
                    request,
                    "Portail: client ou email manquant sur la facture",
                )
            return False

        if not client.has_portal_access:
            if request:
                messages.warning(
                    request,
                    f"Portail: {client.email} n'a pas de compte portail.",
                )
            return False

        if not invoice.pdf:
            invoice.generate_pdf(attach=True)

        title = f"Facture {invoice.number or invoice.id}"
        doc, created = ClientDocument.objects.get_or_create(
            client=client,
            title=title,
            defaults={
                "document_type": "facture",
                "file": invoice.pdf,
                "notes": "Facture publiée depuis l'admin",
            },
        )
        if not created:
            doc.file = invoice.pdf
            doc.save(update_fields=["file"])

        ClientNotification.objects.create(
            client=client,
            notification_type="invoice",
            title=title,
            message="Nouvelle facture disponible dans votre portail client.",
            related_url="/account/documents/",
        )
        return True
    except Exception:
        return False
