"""
Services applicatifs pour l'app ``devis``.

Ce module regroupe la logique métier de haut niveau qui ne doit pas
vivre directement dans les vues ou les modèles Django.

Principales responsabilités :
- Générer une facture à partir d'un devis accepté.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Iterable, Optional, Union

from django.db import transaction

from .models import Quote, QuoteItem
from factures.models import Invoice, InvoiceItem


@dataclass
class InvoiceCreationResult:
    """Résultat de la création d'une facture à partir d'un devis."""

    invoice: Invoice
    quote: Quote


class QuoteAlreadyInvoicedError(Exception):
    """Le devis a déjà été facturé."""


class QuoteStatusError(Exception):
    """Le devis n'est pas dans un état compatible avec la facturation."""


@transaction.atomic
def create_invoice_from_quote(quote: Union[int, Quote]) -> InvoiceCreationResult:
    """
    Crée une facture à partir d'un devis accepté.

    Paramètres
    ----------
    quote :
        Instance de :class:`Quote` ou identifiant primaire du devis.

    Règles métier
    -------------
    - Le devis doit être au statut ``ACCEPTED``.
    - Si une facture existe déjà pour ce devis, une erreur est levée.
    - Les lignes (:class:`QuoteItem`) sont copiées vers
      :class:`factures.models.InvoiceItem` avec leurs valeurs figées.
    - Les totaux HT / TVA / TTC sont recopiés depuis le devis après
      recalcul éventuel.
    - Le statut du devis est passé à ``INVOICED``.
    """
    # Normaliser l'entrée
    if isinstance(quote, int):
        q = Quote.objects.select_related("client").get(pk=quote)
    else:
        q = quote

    # Vérifier le statut
    if q.status != Quote.QuoteStatus.ACCEPTED:
        raise QuoteStatusError(
            f"Le devis {q.pk} n'est pas accepté (statut actuel : {q.status!r})."
        )

    # Vérifier qu'on ne facture pas deux fois le même devis
    if q.invoices.exists():
        raise QuoteAlreadyInvoicedError(
            f"Une facture existe déjà pour le devis {q.pk}."
        )

    # S'assurer que les totaux du devis sont à jour
    if hasattr(q, "compute_totals") and callable(getattr(q, "compute_totals")):
        q.compute_totals()  # type: ignore[call-arg]
        # On recharge les valeurs calculées en base
        q.refresh_from_db(fields=["total_ht", "tva", "total_ttc"])

    # Créer la facture
    invoice = Invoice.objects.create(
        quote=q,
        issue_date=date.today(),
        total_ht=q.total_ht,
        tva=q.tva,
        total_ttc=q.total_ttc,
        discount=Decimal("0.00"),
        amount=q.total_ttc,
        notes=q.message or "",
    )

    # Copier les lignes
    items: Iterable[QuoteItem] = q.quote_items.all()
    for item in items:
        description = item.description or (
            item.service.title if item.service else ""
        )
        # InvoiceItem.quantity est un entier ; on arrondit la quantité
        # du devis à l'entier le plus proche.
        quantity_int = int(round(Decimal(item.quantity)))
        InvoiceItem.objects.create(
            invoice=invoice,
            description=description,
            quantity=quantity_int,
            unit_price=item.unit_price,
            tax_rate=item.tax_rate,
        )

    # Mettre à jour le statut du devis
    q.status = Quote.QuoteStatus.INVOICED
    q.save(update_fields=["status"])

    return InvoiceCreationResult(invoice=invoice, quote=q)
