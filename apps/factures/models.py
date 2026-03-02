"""
factures/models.py — Version rationalisée

✔ Gestion des factures avec numérotation automatique (FAC-AAAA-XXX)
✔ Calcul automatique des totaux (HT, TVA, TTC) avec support des remises
✔ Génération de PDF via InvoicePdfService (WeasyPrint)
✔ Relation vers les devis pour conversion facile
"""
from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from typing import List

from django.db import models
from django.utils.translation import gettext_lazy as _


# =========================
# Helpers
# =========================

def _num2words_fr(v: Decimal) -> str:
    """Montant en toutes lettres (FR). Délègue à core.utils."""
    from core.utils import num2words_fr
    return num2words_fr(v)


# =========================
# Modèles
# =========================

class Invoice(models.Model):

    class InvoiceStatus(models.TextChoices):
        DRAFT = "draft", _("Brouillon")
        REFACTURATION = "refacturation", _("Refacturation")
        AVOIR = "avoir", _("Avoir")
        DEMO = "demo", _("Démonstration")
        SENT = "sent", _("Envoyée")
        PAID = "paid", _("Payée")
        PARTIAL = "partial", _("Partiellement payée")
        OVERDUE = "overdue", _("En retard")

    # Référence en chaîne => évite tout import circulaire
    quote = models.ForeignKey("devis.Quote", on_delete=models.SET_NULL, null=True, blank=True, related_name="invoices")
    client = models.ForeignKey(
        "clients.ClientProfile",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invoices",
        verbose_name=_("Client"),
        help_text="Client facturé (rempli auto depuis le devis).",
    )
    command_ref = models.CharField(max_length=100, blank=True, help_text="Référence bon de commande client.")

    number = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        help_text="Numéro FAC-AAAA-XXX, généré automatiquement si vide."
    )
    issue_date = models.DateField(default=date.today)
    due_date = models.DateField(null=True, blank=True)
    status = models.CharField( max_length=20, choices=InvoiceStatus.choices, default=InvoiceStatus.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)

    # Totaux
    total_ht = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    tva = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    total_ttc = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    # Compat historique
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    # Contenu & sortie
    notes = models.TextField(blank=True, default="")
    payment_terms = models.TextField(blank=True, default="")
    pdf = models.FileField(upload_to="factures", blank=True, null=True)

    # ===========================================
    # PHASE 3 : Paiement en ligne
    # ===========================================
    # Jeton public pour accès client (paiement)
    public_token = models.CharField(
        max_length=64,
        unique=True,
        blank=True,
        null=True,
        help_text="Jeton public pour accès client"
    )
    # Stripe Checkout Session ID
    stripe_checkout_session_id = models.CharField(
        max_length=255,
        blank=True,
        help_text="ID de session Stripe pour le paiement"
    )
    # Montant payé
    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00"),
        help_text="Montant total encaissé"
    )
    # Date du dernier paiement
    paid_at = models.DateTimeField(null=True, blank=True)
    
    # ===========================================
    # Audit trail paiement
    # ===========================================
    paid_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='invoices_marked_paid',
        verbose_name="Marquée payée par",
        help_text="Utilisateur qui a marqué la facture comme payée"
    )
    payment_proof = models.FileField(
        upload_to='factures/proofs/',
        blank=True,
        null=True,
        verbose_name="Preuve de paiement",
        help_text="Document/reçu de paiement (virement, chèque, etc.)"
    )
    payment_audit_trail = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Audit trail paiement",
        help_text="Métadonnées : {ip, user_agent, timestamp, comment, etc.}"
    )

    # ===========================================
    # PHASE 4.3 : Relances automatiques (Dunning)
    # ===========================================
    last_reminder_level = models.IntegerField(
        default=0,
        help_text="Niveau de relance (0=aucune, 1=soft, 2=firm, 3=urgent, 4=final)"
    )
    last_reminder_date = models.DateField(
        null=True,
        blank=True,
        help_text="Date de la dernière relance envoyée"
    )
    reminder_count = models.IntegerField(
        default=0,
        help_text="Nombre total de relances envoyées"
    )
    dunning_completed = models.BooleanField(
        default=False,
        help_text="Processus de relance terminé (4 relances envoyées)"
    )

    class Meta:
        ordering = ["-issue_date", "-number"]
        indexes = [
            models.Index(fields=["number", "issue_date"]),
            models.Index(fields=['status'], name='idx_invoice_status'),
            models.Index(fields=['client', 'status'], name='idx_invoice_client_status'),
            models.Index(fields=['quote'], name='idx_invoice_quote'),
        ]
        verbose_name = _("facture")
        verbose_name_plural = _("factures")

    def __str__(self) -> str:
        return f"Facture {self.number or '—'}"

    def amount_letter(self):
        return  f"{_num2words_fr(self.total_ttc).title()} euros"

    @property
    def items(self) -> List["InvoiceItem"]:
        return list(self.invoice_items.all())

    def save(self, *args, **kwargs) -> None:
        """
        Assignation automatique du numéro de facture, du jeton public,
        et du client depuis le devis si non renseigné.
        """
        import logging
        import secrets

        logger = logging.getLogger(__name__)

        # Remplir le client depuis le devis si manquant
        if not self.client_id and self.quote_id:
            try:
                self.client = self.quote.client
            except (AttributeError, ValueError) as exc:
                logger.warning(
                    "Invoice %s: impossible de résoudre le client depuis le devis: %s",
                    self.pk or '(new)', exc,
                )

        # Générer un jeton public unique (max 10 tentatives)
        if not self.public_token:
            for _ in range(10):
                token = secrets.token_urlsafe(32)
                if not Invoice.objects.filter(public_token=token).exists():
                    self.public_token = token
                    break
            else:
                raise RuntimeError("Impossible de générer un token public unique après 10 tentatives")

        if not self.pk and not self.number:
            year = self.issue_date.year if self.issue_date else date.today().year
            prefix = f"FAC-{year}-"
            from django.db import transaction
            with transaction.atomic():
                last = (
                    Invoice.objects
                    .select_for_update()
                    .filter(number__startswith=prefix)
                    .order_by("number")
                    .last()
                )
                counter = 0
                if last and last.number:
                    try:
                        counter = int(last.number.rsplit("-", 1)[-1])
                    except (ValueError, IndexError):
                        counter = Invoice.objects.filter(number__startswith=prefix).count()
                self.number = f"{prefix}{counter + 1:03d}"
        super().save(*args, **kwargs)

    def compute_totals(self):
        """
        Calcule les totaux HT, TVA et TTC.
        """
        from django.db.models import F, Sum, ExpressionWrapper, DecimalField

        # ⚡ PERFORMANCE: Use DB aggregation instead of Python loop
        agg = self.invoice_items.aggregate(
            sum_ht=Sum(
                ExpressionWrapper(
                    F('quantity') * F('unit_price'),
                    output_field=DecimalField(max_digits=12, decimal_places=2)
                )
            ),
            sum_tva=Sum(
                ExpressionWrapper(
                    F('quantity') * F('unit_price') * F('tax_rate') / Decimal("100"),
                    output_field=DecimalField(max_digits=12, decimal_places=2)
                )
            ),
        )

        total_ht = agg['sum_ht'] or Decimal("0.00")
        total_tva = agg['sum_tva'] or Decimal("0.00")
        
        discount = self.discount or Decimal("0.00")
        if discount > 0 and total_ht > 0:
            if discount > total_ht:
                raise ValueError(f"La remise ({discount}) ne peut pas dépasser le montant HT ({total_ht}).")
            ratio = (discount / total_ht).quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)
            total_ht -= discount
            total_tva -= (total_tva * ratio)

        if total_ht < 0: total_ht = Decimal("0.00")
        if total_tva < 0: total_tva = Decimal("0.00")
        
        self.total_ht = total_ht.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        self.tva = total_tva.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        self.total_ttc = (self.total_ht + self.tva).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        self.amount = self.total_ttc
        self.save(update_fields=["total_ht", "tva", "total_ttc", "amount"])

    def generate_pdf(self, attach: bool = True) -> bytes:
        """
        Génère le PDF de la facture via DocumentGenerator.
        """
        from core.services.document_generator import DocumentGenerator
        return DocumentGenerator.generate_invoice_pdf(self, attach=attach)


class InvoiceItem(models.Model):
    """Ligne de facture."""
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="invoice_items")
    description = models.CharField(max_length=255, blank=True)
    quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("1.00"))
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))

    class Meta:
        verbose_name = _("ligne de facture")
        verbose_name_plural = _("lignes de facture")

    def __str__(self) -> str:
        return self.description or "Ligne"

    @property
    def total_ht(self) -> Decimal:
        return (self.unit_price * self.quantity).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @property
    def total_tva(self) -> Decimal:
        return (self.total_ht * self.tax_rate / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @property
    def total_ttc(self) -> Decimal:
        return (self.total_ht + self.total_tva).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
