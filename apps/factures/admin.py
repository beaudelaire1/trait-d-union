"""
Configuration de l'administration pour l'app ``factures``.

Cette configuration permet de générer des PDF pour les factures sélectionnées
directement depuis la liste dans l'admin et de visualiser les attributs
principaux (numéro, devis associé, montant, date).
"""

from django.contrib import admin
from django.utils.html import format_html
from django.core.files.base import ContentFile
from django import forms
import os
from django.urls import reverse

from .models import Invoice, InvoiceItem
from .services import PremiumEmailService


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
    list_display = ("number", "quote", "status", "issue_date", "total_ttc", "pdf_link")
    list_filter = ("status", "issue_date")
    search_fields = ("number", "quote__client__full_name")
    readonly_fields = ("total_ht", "tva", "total_ttc", "issue_date", "created_at")
    actions = ["generate_pdfs", "send_invoices"]

    class InvoiceItemInline(admin.TabularInline):
        model = InvoiceItem
        extra = 1
        fields = (
            "description",
            "quantity",
            "unit_price",
            "tax_rate",
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
