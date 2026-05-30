"""
Calcul réglementaire de la TVA pour la facturation électronique (EN 16931).

Cette couche est la SEULE source autorisée pour le calcul des bases HT, des
montants de TVA, et de la breakdown par catégorie utilisée dans les XML CII /
UBL. Elle est volontairement séparée de `Invoice.compute_totals()` (qui reste
une vue agrégée monobase pour l'affichage) car la facture électronique exige
une décomposition par couple `(category, rate, exemption_reason)`.

Mappings réglementaires :
- BT-106 : Sum of Invoice line net amount  (Σ HT lignes après remise ligne)
- BT-109 : Invoice total amount without VAT  (BT-106 - remise globale)
- BT-110 : Invoice total VAT amount
- BT-112 : Invoice total amount with VAT
- BT-115 : Amount due for payment
- BG-23 (Vat Breakdown):
    BT-116 : Taxable amount
    BT-117 : VAT category tax amount
    BT-118 : VAT category code (S/Z/E/AE/K/G/O)
    BT-119 : VAT category rate
    BT-120 / BT-121 : Exemption reason text + code (VATEX-EU-*)

Régime fiscal : la catégorie VAT et le code VATEX par défaut sont déduits du
régime actif (`apps.einvoicing.legal`) et JAMAIS hardcodés dans ce module.

Cas TUS (Guyane, art. 294 CGI) :
- vat_category_code = O (Outside scope of VAT)
- vat_exemption_reason_code = VATEX-EU-O
- BT-117 / BT-110 = 0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from typing import TYPE_CHECKING, List, Optional

from .codelists import VATEX_REASON_CODES

if TYPE_CHECKING:  # pragma: no cover
    from apps.factures.models import Invoice


TWO_PLACES = Decimal("0.01")
ZERO = Decimal("0")


def q2(value: Decimal) -> Decimal:
    """Quantize 2 décimales, half-up — règle d'arrondi EN 16931 / Factur-X."""
    return Decimal(value).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)


@dataclass(frozen=True)
class VATBreakdownLine:
    """Une ligne BG-23 (VAT Breakdown) du XML."""

    category_code: str          # BT-118 (S/Z/E/AE/K/G/O)
    rate_percent: Decimal       # BT-119 (ex. Decimal("20.00"))
    taxable_amount: Decimal     # BT-116
    tax_amount: Decimal         # BT-117
    exemption_reason_code: str = ""  # BT-121 (VATEX-EU-*)
    exemption_reason_text: str = ""  # BT-120


@dataclass(frozen=True)
class InvoiceTotals:
    """Vue compacte des totaux EN 16931 d'une facture."""

    line_net_total: Decimal     # BT-106
    allowance_total: Decimal    # BT-107 (remises globales documentaires)
    charge_total: Decimal       # BT-108 (frais globaux)
    tax_basis_total: Decimal    # BT-109
    tax_total: Decimal          # BT-110
    grand_total: Decimal        # BT-112
    paid_amount: Decimal        # BT-113 (déjà encaissé)
    rounding_amount: Decimal    # BT-114
    payable_amount: Decimal     # BT-115
    breakdown: List[VATBreakdownLine] = field(default_factory=list)


def _line_taxable_amount(item) -> Decimal:
    """Calcule HT net de la ligne (après remise) sans réécrire compute_totals.

    On reproduit la formule existante de InvoiceItem.total_ht :
        HT_net = qty * unit_price * (1 - line_discount/100)
    Si l'objet expose déjà `total_ht`, on l'utilise (évite les surprises).
    """
    if hasattr(item, "total_ht"):
        # `total_ht` est une propriété quantizée → on la déquantize pour cumul propre
        return Decimal(item.total_ht)
    qty = Decimal(item.quantity or 0)
    pu = Decimal(item.unit_price or 0)
    disc = Decimal(item.line_discount or 0) / Decimal("100")
    return qty * pu * (Decimal("1") - disc)


def _line_category(item, default_category: Optional[str] = None) -> str:
    """Catégorie TVA à utiliser pour cette ligne. Tombe sur le défaut sinon."""
    from .legal import get_default_vat_category
    return getattr(item, "vat_category_code", "") or default_category or get_default_vat_category()


def _line_reason_code(item) -> str:
    """Motif d'exemption VATEX. Si la ligne ne précise rien, on déduit du régime actif."""
    from .legal import get_default_vatex_code
    return getattr(item, "vat_exemption_reason_code", "") or get_default_vatex_code()


def compute_vat_breakdown(invoice: "Invoice") -> InvoiceTotals:
    """Construit l'agrégat TVA EN 16931 pour la facture.

    Les lignes sont groupées par couple `(category, rate, exemption_reason)`.
    Le résultat est déterministe (tri lexicographique par catégorie puis taux).
    """
    items = list(invoice.invoice_items.all().only(
        "quantity", "unit_price", "tax_rate", "line_discount",
        "vat_category_code", "vat_exemption_reason_code",
    ))

    # Agrégation par (category, rate, reason)
    buckets: dict[tuple[str, Decimal, str], dict[str, Decimal]] = {}
    line_net_total = ZERO
    for item in items:
        category = _line_category(item)
        rate = Decimal(item.tax_rate or 0).quantize(Decimal("0.01"))
        reason = _line_reason_code(item)
        net = _line_taxable_amount(item)
        line_net_total += net
        key = (category, rate, reason)
        bucket = buckets.setdefault(key, {"taxable": ZERO, "tax": ZERO})
        bucket["taxable"] += net
        bucket["tax"] += net * rate / Decimal("100")

    # Remise globale (champ `discount` historique de Invoice)
    allowance_total = Decimal(getattr(invoice, "discount", 0) or 0)

    # On répartit la remise globale au prorata des bases (best-effort, sans toucher
    # à l'arrondi général) — alignement avec compute_totals existant.
    if allowance_total > 0 and line_net_total > 0:
        ratio = allowance_total / line_net_total
        for k, b in buckets.items():
            b["taxable"] = b["taxable"] - (b["taxable"] * ratio)
            b["tax"] = b["tax"] - (b["tax"] * ratio)

    breakdown = [
        VATBreakdownLine(
            category_code=cat,
            rate_percent=rate,
            taxable_amount=q2(b["taxable"]),
            tax_amount=q2(b["tax"]),
            exemption_reason_code=reason,
            exemption_reason_text=VATEX_REASON_CODES.get(reason, "")[:1000] if reason else "",
        )
        for (cat, rate, reason), b in sorted(buckets.items(), key=lambda kv: (kv[0][0], kv[0][1]))
    ]

    tax_basis_total = q2(line_net_total - allowance_total)
    tax_total = q2(sum((bl.tax_amount for bl in breakdown), ZERO))
    grand_total = q2(tax_basis_total + tax_total)
    paid_amount = q2(Decimal(getattr(invoice, "amount_paid", 0) or 0))
    payable_amount = q2(grand_total - paid_amount)

    return InvoiceTotals(
        line_net_total=q2(line_net_total),
        allowance_total=q2(allowance_total),
        charge_total=ZERO,  # pas de "frais globaux" dans le modèle actuel
        tax_basis_total=tax_basis_total,
        tax_total=tax_total,
        grand_total=grand_total,
        paid_amount=paid_amount,
        rounding_amount=ZERO,
        payable_amount=payable_amount,
        breakdown=breakdown,
    )


__all__ = [
    "compute_vat_breakdown",
    "InvoiceTotals",
    "VATBreakdownLine",
    "q2",
]
