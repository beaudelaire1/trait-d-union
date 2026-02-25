from django.contrib import admin, messages
from django.urls import path, reverse
from django.shortcuts import get_object_or_404, redirect
from django.utils.html import format_html
from django import forms
from django.contrib.auth.models import User
from apps.clients.models import ClientDocument, ClientNotification
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
    """Administration des clients — avec création rapide de compte portail."""
    
    list_display = ('full_name', 'email', 'phone', 'city', 'portal_account_badge', 'created_at')
    list_filter = ('created_at', 'city')
    search_fields = ('full_name', 'email', 'phone', 'city', 'address_line')
    readonly_fields = ('created_at',)
    actions = ['action_create_portal_account']
    
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

    def portal_account_badge(self, obj):
        """Affiche si le client a déjà un compte portail."""
        if not obj.email:
            return format_html(
                '<span style="color:#6B7280; font-size:0.8rem;">—</span>'
            )
        user = User.objects.filter(email__iexact=obj.email).first()
        if user and hasattr(user, 'client_profile'):
            return format_html(
                '<span style="background:rgba(34,197,94,0.15); color:#4ADE80; '
                'padding:3px 10px; border-radius:12px; font-size:0.75rem; '
                'font-weight:600;">✅ Compte actif</span>'
            )
        return format_html(
            '<span style="background:rgba(107,114,128,0.15); color:#9CA3AF; '
            'padding:3px 10px; border-radius:12px; font-size:0.75rem; '
            'font-weight:600;">Aucun compte</span>'
        )
    portal_account_badge.short_description = "Portail TUS"

    @admin.action(description="👤 Créer le compte portail client")
    def action_create_portal_account(self, request, queryset):
        """Crée un compte portail (User + ClientProfile) pour les contacts sélectionnés.
        
        - Génère un mot de passe temporaire
        - Envoie l'email de bienvenue
        - Le client devra changer son mot de passe à la première connexion
        """
        from apps.clients.services import create_client_account, ClientAccountError

        created = 0
        skipped = 0
        errors = []

        for client in queryset:
            if not client.email:
                errors.append(f"{client.full_name}: pas d'email")
                continue

            try:
                result = create_client_account(
                    email=client.email,
                    full_name=client.full_name,
                    company_name=client.company or '',
                    phone=client.phone or '',
                    address=f"{client.address_line} {client.city} {client.zip_code}".strip(),
                    send_email=True,
                )
                if result.is_new:
                    created += 1
                else:
                    skipped += 1
            except ClientAccountError as e:
                errors.append(f"{client.full_name}: {e}")

        if created:
            messages.success(
                request,
                f"✅ {created} compte(s) client créé(s) — email de bienvenue envoyé."
            )
        if skipped:
            messages.info(
                request,
                f"ℹ️ {skipped} contact(s) avai(en)t déjà un compte portail."
            )
        for err in errors:
            messages.warning(request, f"⚠️ {err}")


@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    form = QuoteAdminForm
    list_display = ("number", "client", "status", "total_ttc", "pdf_link")
    inlines = [QuoteItemInline]

    def save_related(self, request, form, formsets, change):
        """Recalcule les totaux après sauvegarde des lignes de devis."""
        super().save_related(request, form, formsets, change)
        form.instance.compute_totals()

    actions = [
        "action_generate_pdf",
        "action_convert_to_invoice",
        "action_send_quote_email",
        "action_validate_and_create_account",
        "action_generate_pdf_and_publish",
        "action_send_quote_email_and_publish",
        "action_convert_to_invoice_and_publish",
    ]

    def pdf_link(self, obj: Quote) -> str:
        """Retourne un lien vers la vue de téléchargement du PDF (généré à la volée)."""
        url = reverse("devis:download", args=[obj.pk])
        return format_html("<a href='{}' target='_blank'>Ouvrir</a>", url)
    pdf_link.short_description = "PDF"

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
        self._publish_to_portal(quote, request)
        return redirect(reverse("admin:devis_quote_change", args=[quote.pk]))

    def _view_send_email(self, request, pk: int):
        from core.tasks import async_send_quote_email
        quote = get_object_or_404(Quote, pk=pk)
        if not quote.pdf:
            quote.generate_pdf(attach=True)
        async_send_quote_email(quote.pk)
        self.message_user(request, "Email devis en cours d'envoi.", level=messages.SUCCESS)
        self._publish_to_portal(quote, request)
        return redirect(reverse("admin:devis_quote_change", args=[quote.pk]))

    def _view_convert_invoice(self, request, pk: int):
        quote = get_object_or_404(Quote, pk=pk)
        invoice = quote.convert_to_invoice()
        self.message_user(request, f"Devis converti en facture : {invoice.number}", level=messages.SUCCESS)
        self._publish_to_portal(quote, request)
        return redirect(reverse("admin:factures_invoice_change", args=[invoice.pk]))

    @admin.action(description="📄 Générer le devis en PDF")
    def action_generate_pdf(self, request, queryset):
        for quote in queryset:
            if hasattr(quote, "generate_pdf"):
                quote.generate_pdf()
        self.message_user(request, "PDF généré.", level=messages.SUCCESS)

    @admin.action(description="✅ Valider le devis → créer le compte client")
    def action_validate_and_create_account(self, request, queryset):
        """Valide les devis sélectionnés (SENT → VALIDATED) et crée le compte client.
        
        Flux complet :
        1. Vérifie que le devis est au statut SENT
        2. Passe en VALIDATED (via validate_quote use case)
        3. Crée le compte User + ClientProfile (via provision_client_account)
        4. Envoie l'email de bienvenue avec mot de passe temporaire
        5. Le client devra changer son mot de passe à la première connexion
        """
        from apps.devis.application.validate_quote_usecase import (
            validate_quote, provision_client_account,
            QuoteValidationError, ClientAccountProvisionError
        )
        
        validated = 0
        accounts_created = 0
        errors = []
        
        for quote in queryset:
            # 1. Valider le devis
            try:
                validate_quote(quote, validated_by=request.user, request=request)
                validated += 1
            except QuoteValidationError as e:
                errors.append(f"{quote.number}: {e}")
                continue
            
            # 2. Créer le compte client (le signal le fait aussi, mais on force ici)
            try:
                result = provision_client_account(quote, request=request)
                if result.is_new:
                    accounts_created += 1
                    self.message_user(
                        request,
                        f"👤 Compte client créé : {result.user.email} "
                        f"(mot de passe temporaire envoyé par email)",
                        level=messages.SUCCESS,
                    )
            except ClientAccountProvisionError as e:
                errors.append(f"{quote.number} (compte): {e}")
            
            # 3. Publier le devis sur le portail
            self._publish_to_portal(quote, request)
        
        if validated:
            self.message_user(
                request,
                f"✅ {validated} devis validé(s). {accounts_created} compte(s) client créé(s).",
                level=messages.SUCCESS,
            )
        for err in errors:
            self.message_user(request, f"⚠️ {err}", level=messages.WARNING)

    @admin.action(description="📄 Générer le devis en PDF et publier sur portail")
    def action_generate_pdf_and_publish(self, request, queryset):
        published = 0
        for quote in queryset:
            if hasattr(quote, "generate_pdf"):
                quote.generate_pdf(attach=True)
                if self._publish_to_portal(quote, request):
                    published += 1
        self.message_user(request, f"PDF généré. {published} publié(s) sur le portail.", level=messages.SUCCESS)

    @admin.action(description="🧾 Convertir en facture")
    def action_convert_to_invoice(self, request, queryset):
        for quote in queryset:
            if hasattr(quote, "convert_to_invoice"):
                invoice = quote.convert_to_invoice()
                self.message_user(request, f"{quote.number} → {invoice.number}", level=messages.SUCCESS)
        self.message_user(request, "Devis converti en facture.", level=messages.SUCCESS)

    @admin.action(description="🧾 Convertir en facture et publier sur portail")
    def action_convert_to_invoice_and_publish(self, request, queryset):
        published = 0
        for quote in queryset:
            if hasattr(quote, "convert_to_invoice"):
                invoice = quote.convert_to_invoice()
                if self._publish_to_portal(quote, request):
                    published += 1
                # Publier aussi la facture si possible
                try:
                    from apps.factures.admin import publish_invoice_to_portal
                    if publish_invoice_to_portal(invoice, request):
                        published += 1
                except Exception:
                    pass
        self.message_user(request, f"Devis converti. {published} document(s) publié(s) sur le portail.", level=messages.SUCCESS)

    @admin.action(description="📧 Envoyer le devis par email")
    def action_send_quote_email(self, request, queryset):
        from core.tasks import async_send_quote_email
        count = 0
        for quote in queryset:
            if not quote.pdf:
                quote.generate_pdf(attach=True)
            async_send_quote_email(quote.pk)
            count += 1
        self.message_user(request, f"{count} devis en cours d'envoi par email.", level=messages.SUCCESS)

    @admin.action(description="📧 Envoyer le devis et publier sur portail")
    def action_send_quote_email_and_publish(self, request, queryset):
        from core.tasks import async_send_quote_email
        published = 0
        for quote in queryset:
            if not quote.pdf:
                quote.generate_pdf(attach=True)
            async_send_quote_email(quote.pk)
            if self._publish_to_portal(quote, request):
                published += 1
        self.message_user(request, f"Devis en cours d'envoi. {published} publié(s) sur le portail.", level=messages.SUCCESS)

    def _publish_to_portal(self, quote: Quote, request) -> bool:
        """Publie le PDF du devis dans le portail client (ClientDocument + notification).

        Stratégie :
        - On cherche un User par email du devis (case-insensitive)
        - On prend son ClientProfile
        - On crée un ClientDocument (type "contract") avec le PDF
        - On envoie une notification portail
        """
        try:
            if not quote.client or not quote.client.email:
                self.message_user(
                    request,
                    "Portail: client ou email manquant sur le devis",
                    level=messages.WARNING,
                )
                return False

            user = User.objects.filter(email__iexact=quote.client.email).first()
            client_profile = getattr(user, "client_profile", None) if user else None
            if not client_profile:
                self.message_user(
                    request,
                    f"Portail: aucun client trouvé pour {quote.client.email}",
                    level=messages.WARNING,
                )
                return False

            if not quote.pdf:
                quote.generate_pdf(attach=True)

            title = f"Devis {quote.number or quote.id}"
            doc, created = ClientDocument.objects.get_or_create(
                client=client_profile,
                title=title,
                defaults={
                    "document_type": "devis",
                    "file": quote.pdf,
                    "notes": "Devis publié depuis l'admin",
                },
            )
            if not created:
                # mettre à jour le fichier si déjà existant
                doc.file = quote.pdf
                doc.save(update_fields=["file"])

            ClientNotification.objects.create(
                client=client_profile,
                notification_type="quote",
                title=title,
                message="Nouveau devis disponible dans votre portail client.",
                related_url="/account/documents/",
            )
            return True
        except Exception:
            # on évite de bloquer l'action principale
            return False

# NOTE : on ne register pas QuoteItem pour éviter un menu séparé en admin.