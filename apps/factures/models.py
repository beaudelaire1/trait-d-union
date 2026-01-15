"""
factures/models.py — Version rationalisée

✔ Gestion des factures avec numérotation automatique (FAC-AAAA-XXX)
✔ Calcul automatique des totaux (HT, TVA, TTC) avec support des remises
✔ Génération de PDF via InvoicePdfService (WeasyPrint)
✔ Relation vers les devis pour conversion facile
"""
import os
from decimal import Decimal, ROUND_HALF_UP
from datetime import date
from typing import List, Optional

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.files.base import ContentFile


# =========================
# Helpers
# =========================

def _num2words_fr(v: Decimal) -> str:
    """Import tardif de .utils.num2words_fr, repli numérique FR si absent."""
    try:
        from .utils import num2words_fr as _n2w
        return _n2w(v)
    except Exception:
        return str(v).replace(".", ",")


# =========================
# Modèles
# =========================

class Invoice(models.Model):

    class InvoiceStatus(models.TextChoices):
        DRAFT = "draft", _("Brouillon")
        REFACTURATION = "refacturation", _("Refacturation")
        AVOIR = "avoir", _("Avoir")
        DEMO = "demo", _("Devis")
        SENT = "sent", _("Envoyée")
        PAID = "paid", _("Payée")
        PARTIAL = "partial", _("Partiellement payée")
        OVERDUE = "overdue", _("En retard")

    # Référence en chaîne => évite tout import circulaire
    quote = models.ForeignKey("devis.Quote", on_delete=models.SET_NULL, null=True, blank=True, related_name="invoices")
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

    class Meta:
        ordering = ["-issue_date", "-number"]
        indexes = [models.Index(fields=["number", "issue_date"])]
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
        Assignation automatique du numéro de facture.
        """
        if not self.pk and not self.number:
            year = self.issue_date.year if getattr(self, "issue_date", None) else date.today().year
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
                if last:
                    try:
                        counter = int(str(last.number).split("-")[-1])
                    except Exception:
                        counter = 0
                self.number = f"{prefix}{counter + 1:03d}"
        super().save(*args, **kwargs)

    def compute_totals(self):
        """
        Calcule les totaux HT, TVA et TTC.
        """
        total_ht = Decimal("0.00")
        total_tva = Decimal("0.00")
        for it in self.items:
            total_ht += it.total_ht
            total_tva += it.total_tva
        
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
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))

    class Meta:
        verbose_name = _("ligne de facture")
        verbose_name_plural = _("lignes de facture")

    def __str__(self) -> str:
        return self.description or "Ligne"

    @property
    def total_ht(self) -> Decimal:
        return (self.unit_price * Decimal(self.quantity)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @property
    def total_tva(self) -> Decimal:
        return (self.total_ht * self.tax_rate / Decimal("100")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @property
    def total_ttc(self) -> Decimal:
        return (self.total_ht + self.total_tva).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
