from django.contrib import admin, messages
from django.urls import path, reverse
from django.shortcuts import get_object_or_404, redirect
from django import forms
from .models import Quote, QuoteItem, Client


class QuoteAdminForm(forms.ModelForm):
    """Custom admin form for Quote with Textarea for notes field."""
    
    notes = forms.CharField(
        label="Notes internes",
        widget=forms.Textarea(attrs={'cols': 80, 'rows': 15}),
        required=False,
        help_text="Notes internes pour le devis"
    )
    
    class Meta:
        model = Quote
        fields = '__all__'


class QuoteItemInline(admin.TabularInline):
    """Lignes de devis *incluses* dans la fiche devis (comme une facture).

    Exigence : ne pas avoir une section/liste séparée "lignes de devis" dans
    l'admin. Les lignes se gèrent directement dans le devis.
    """

    model = QuoteItem
    extra = 1
    autocomplete_fields = ("service",)
    fields = ("service", "description", "quantity", "unit_price", "tax_rate")


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    """Administration des clients."""
    
    list_display = ('full_name', 'email', 'phone', 'city', 'created_at')
    list_filter = ('created_at', 'city')
    search_fields = ('full_name', 'email', 'phone', 'city', 'address_line')
    readonly_fields = ('created_at',)
    
    fieldsets = (
        ('Informations personnelles', {
            'fields': ('full_name', 'email', 'phone', 'company')
        }),
        ('Adresse', {
            'fields': ('address_line', 'city', 'zip_code')
        }),
        ('Informations système', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    form = QuoteAdminForm
    list_display = ("number", "client", "status", "total_ttc", "pdf")
    inlines = [QuoteItemInline]

    actions = [
        "action_generate_pdf",
        "action_convert_to_invoice",
        "action_send_quote_email",
    ]

    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path(
                "<int:pk>/generate-pdf/",
                self.admin_site.admin_view(self._view_generate_pdf),
                name="quote-generate-pdf",
            ),
            path(
                "<int:pk>/send-email/",
                self.admin_site.admin_view(self._view_send_email),
                name="quote-send-email",
            ),
            path(
                "<int:pk>/convert-invoice/",
                self.admin_site.admin_view(self._view_convert_invoice),
                name="quote-convert-invoice",
            ),
        ]
        return custom + urls

    def _view_generate_pdf(self, request, pk: int):
        quote = get_object_or_404(Quote, pk=pk)
        quote.generate_pdf(attach=True)
        self.message_user(request, "PDF devis généré.", level=messages.SUCCESS)
        return redirect(reverse("admin:devis_quote_change", args=[quote.pk]))

    def _view_send_email(self, request, pk: int):
        quote = get_object_or_404(Quote, pk=pk)
        quote.send_email(request=request, force_pdf=True)
        self.message_user(request, "Email devis envoyé.", level=messages.SUCCESS)
        return redirect(reverse("admin:devis_quote_change", args=[quote.pk]))

    def _view_convert_invoice(self, request, pk: int):
        quote = get_object_or_404(Quote, pk=pk)
        invoice = quote.convert_to_invoice()
        self.message_user(request, f"Devis converti en facture : {invoice.number}", level=messages.SUCCESS)
        return redirect(f"/admin/factures/invoice/{invoice.pk}/change/")

    @admin.action(description="📄 Générer le devis en PDF")
    def action_generate_pdf(self, request, queryset):
        for quote in queryset:
            if hasattr(quote, "generate_pdf"):
                quote.generate_pdf()
        self.message_user(request, "PDF généré.", level=messages.SUCCESS)

    @admin.action(description="🧾 Convertir en facture")
    def action_convert_to_invoice(self, request, queryset):
        for quote in queryset:
            if hasattr(quote, "convert_to_invoice"):
                invoice = quote.convert_to_invoice()
                self.message_user(request, f"{quote.number} → {invoice.number}", level=messages.SUCCESS)
        self.message_user(request, "Devis converti en facture.", level=messages.SUCCESS)

    @admin.action(description="📧 Envoyer le devis par email")
    def action_send_quote_email(self, request, queryset):
        for quote in queryset:
            if hasattr(quote, "send_email"):
                quote.send_email(request=request, force_pdf=True)
        self.message_user(request, "Devis envoyés par email.", level=messages.SUCCESS)

# NOTE : on ne register pas QuoteItem pour éviter un menu séparé en admin.