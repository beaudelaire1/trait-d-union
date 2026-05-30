"""Tests d'agrégation TVA EN 16931 (BG-23 / BT-110/116/117)."""

from __future__ import annotations

from decimal import Decimal

import pytest

from apps.clients.models import ClientProfile
from apps.einvoicing.codelists import VATCategory
from apps.einvoicing.taxation import compute_vat_breakdown, q2
from apps.factures.models import Invoice, InvoiceItem


pytestmark = pytest.mark.django_db


def _client():
    return ClientProfile.objects.create(full_name="Acme", email="acme@example.com")


def _make_invoice_with_items(items_data: list[dict]) -> Invoice:
    inv = Invoice.objects.create(client=_client())
    for data in items_data:
        InvoiceItem.objects.create(invoice=inv, **data)
    inv.compute_totals()
    return inv


class TestVATBreakdown:
    def test_franchise_en_base_tus(self) -> None:
        """TUS franchise en base : tout est exonéré (E + VATEX-EU-79-C, taux 0)."""
        inv = _make_invoice_with_items([
            {
                "description": "Audit accessibilité",
                "quantity": Decimal("1"),
                "unit_price": Decimal("1500.00"),
                "tax_rate": Decimal("0"),
                "vat_category_code": VATCategory.EXEMPT,
                "vat_exemption_reason_code": "VATEX-EU-79-C",
            },
            {
                "description": "Refonte site",
                "quantity": Decimal("1"),
                "unit_price": Decimal("3500.00"),
                "tax_rate": Decimal("0"),
                "vat_category_code": VATCategory.EXEMPT,
                "vat_exemption_reason_code": "VATEX-EU-79-C",
            },
        ])
        totals = compute_vat_breakdown(inv)
        assert totals.tax_total == q2(Decimal("0"))
        assert totals.line_net_total == q2(Decimal("5000.00"))
        assert totals.grand_total == q2(Decimal("5000.00"))
        assert totals.payable_amount == q2(Decimal("5000.00"))
        assert len(totals.breakdown) == 1
        b = totals.breakdown[0]
        assert b.category_code == "E"
        assert b.exemption_reason_code == "VATEX-EU-79-C"
        assert b.tax_amount == q2(Decimal("0"))

    def test_multi_rate_invoice(self) -> None:
        """Cas standard à plusieurs taux (20% + 10%)."""
        inv = _make_invoice_with_items([
            {
                "description": "Service A",
                "quantity": Decimal("1"),
                "unit_price": Decimal("1000.00"),
                "tax_rate": Decimal("20.00"),
                "vat_category_code": VATCategory.STANDARD,
            },
            {
                "description": "Service B",
                "quantity": Decimal("1"),
                "unit_price": Decimal("500.00"),
                "tax_rate": Decimal("10.00"),
                "vat_category_code": VATCategory.STANDARD,
            },
        ])
        totals = compute_vat_breakdown(inv)
        assert totals.line_net_total == q2(Decimal("1500.00"))
        assert totals.tax_total == q2(Decimal("250.00"))
        assert totals.grand_total == q2(Decimal("1750.00"))
        # Deux buckets distincts par taux
        assert len(totals.breakdown) == 2
        rates = {b.rate_percent for b in totals.breakdown}
        assert Decimal("20.00") in rates and Decimal("10.00") in rates

    def test_quantity_and_discount(self) -> None:
        """Remise ligne et quantité : net HT = qty * pu * (1 - disc/100)."""
        inv = _make_invoice_with_items([
            {
                "description": "Article",
                "quantity": Decimal("3"),
                "unit_price": Decimal("100.00"),
                "tax_rate": Decimal("20.00"),
                "line_discount": Decimal("10.00"),
                "vat_category_code": VATCategory.STANDARD,
            },
        ])
        # net = 3 * 100 * 0.9 = 270
        # tva = 270 * 0.20 = 54
        totals = compute_vat_breakdown(inv)
        assert totals.line_net_total == q2(Decimal("270.00"))
        assert totals.tax_total == q2(Decimal("54.00"))
        assert totals.grand_total == q2(Decimal("324.00"))

    def test_payable_amount_after_prepayment(self) -> None:
        inv = _make_invoice_with_items([
            {
                "description": "X",
                "quantity": Decimal("1"),
                "unit_price": Decimal("1000.00"),
                "tax_rate": Decimal("20.00"),
                "vat_category_code": VATCategory.STANDARD,
            },
        ])
        inv.amount_paid = Decimal("400.00")
        inv.save(update_fields=["amount_paid"])
        totals = compute_vat_breakdown(inv)
        assert totals.grand_total == q2(Decimal("1200.00"))
        assert totals.paid_amount == q2(Decimal("400.00"))
        assert totals.payable_amount == q2(Decimal("800.00"))
