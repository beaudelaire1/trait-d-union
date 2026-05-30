"""Tests du builder XML CII (Factur-X profile EN 16931)."""

from __future__ import annotations

from decimal import Decimal

import pytest
from lxml import etree

from apps.clients.models import ClientProfile
from apps.einvoicing.builders.cii import NS, build_cii_xml
from apps.factures.models import Invoice, InvoiceItem


pytestmark = pytest.mark.django_db


def _xpath(root, expr: str):
    return root.xpath(expr, namespaces={k: v for k, v in NS.items() if k})


def _make_invoice_min() -> Invoice:
    client = ClientProfile.objects.create(
        full_name="Acme SARL",
        email="acme@example.com",
        company_name="Acme SARL",
        is_business=True,
        country_code="FR",
        siren="908264112",
        siret="90826411200016",
        address_line="1 rue de Paris",
        city="Paris",
        zip_code="75001",
    )
    inv = Invoice.objects.create(
        client=client,
        buyer_reference="REF-XYZ-001",
        purchase_order_ref="PO-2026-42",
    )
    InvoiceItem.objects.create(
        invoice=inv,
        description="Refonte du site",
        quantity=Decimal("1"),
        unit_price=Decimal("4500.00"),
        tax_rate=Decimal("0"),
        vat_category_code="E",
        vat_exemption_reason_code="VATEX-EU-79-C",
    )
    inv.compute_totals()
    return inv


class TestCIIBuilderShape:
    def test_xml_is_well_formed_and_root(self) -> None:
        xml = build_cii_xml(_make_invoice_min())
        assert xml.startswith(b"<?xml")
        root = etree.fromstring(xml)
        assert root.tag.endswith("CrossIndustryInvoice")

    def test_profile_urn_is_en16931(self) -> None:
        xml = build_cii_xml(_make_invoice_min())
        root = etree.fromstring(xml)
        urn = _xpath(
            root,
            "//rsm:ExchangedDocumentContext/ram:GuidelineSpecifiedDocumentContextParameter/ram:ID/text()",
        )
        assert urn and "en16931" in urn[0]

    def test_invoice_id_and_typecode(self) -> None:
        inv = _make_invoice_min()
        root = etree.fromstring(build_cii_xml(inv))
        assert _xpath(root, "//rsm:ExchangedDocument/ram:ID/text()") == [inv.number]
        assert _xpath(root, "//rsm:ExchangedDocument/ram:TypeCode/text()") == [inv.invoice_type_code]

    def test_buyer_party_includes_siren_and_name(self) -> None:
        inv = _make_invoice_min()
        root = etree.fromstring(build_cii_xml(inv))
        names = _xpath(root, "//ram:BuyerTradeParty/ram:Name/text()")
        assert names and "Acme" in names[0]
        # SIRET ou SIREN doit apparaître quelque part comme ID (BT-46)
        ids = _xpath(root, "//ram:BuyerTradeParty/ram:ID/text()")
        assert ids and (ids[0] == "90826411200016" or ids[0].startswith("908264112"))

    def test_buyer_reference_present(self) -> None:
        inv = _make_invoice_min()
        root = etree.fromstring(build_cii_xml(inv))
        refs = _xpath(root, "//ram:ApplicableHeaderTradeAgreement/ram:BuyerReference/text()")
        assert refs == ["REF-XYZ-001"]

    def test_purchase_order_present(self) -> None:
        inv = _make_invoice_min()
        root = etree.fromstring(build_cii_xml(inv))
        po = _xpath(root, "//ram:BuyerOrderReferencedDocument/ram:IssuerAssignedID/text()")
        assert po == ["PO-2026-42"]

    def test_quote_reference_in_xml(self) -> None:
        """BT-14 — Sales order reference : devis lié encodé dans le XML."""
        from apps.devis.models import Quote, QuoteItem
        from apps.devis.services import create_invoice_from_quote
        client = ClientProfile.objects.create(
            full_name="Acme",
            email="acme@example.com",
            company_name="Acme",
            is_business=True,
            country_code="FR",
        )
        quote = Quote.objects.create(client=client, status=Quote.QuoteStatus.ACCEPTED)
        QuoteItem.objects.create(
            quote=quote,
            description="Service",
            quantity=Decimal("1"),
            unit_price=Decimal("100.00"),
            tax_rate=Decimal("0"),
        )
        quote.compute_totals()
        invoice = create_invoice_from_quote(quote).invoice
        root = etree.fromstring(build_cii_xml(invoice))
        sor = _xpath(root, "//ram:SellerOrderReferencedDocument/ram:IssuerAssignedID/text()")
        assert sor == [quote.number]


class TestCIIBuilderFranchiseEnBase:
    def test_vat_category_e_with_vatex_reason(self) -> None:
        inv = _make_invoice_min()
        root = etree.fromstring(build_cii_xml(inv))
        # Au moins un breakdown TVA présent au niveau Settlement
        cats = _xpath(
            root,
            "//ram:ApplicableHeaderTradeSettlement/ram:ApplicableTradeTax/ram:CategoryCode/text()",
        )
        assert "E" in cats
        reasons = _xpath(
            root,
            "//ram:ApplicableHeaderTradeSettlement/ram:ApplicableTradeTax/ram:ExemptionReasonCode/text()",
        )
        assert "VATEX-EU-79-C" in reasons

    def test_grand_total_equals_line_total_no_vat(self) -> None:
        inv = _make_invoice_min()
        root = etree.fromstring(build_cii_xml(inv))
        line_total = _xpath(
            root,
            "//ram:SpecifiedTradeSettlementHeaderMonetarySummation/ram:LineTotalAmount/text()",
        )
        grand = _xpath(
            root,
            "//ram:SpecifiedTradeSettlementHeaderMonetarySummation/ram:GrandTotalAmount/text()",
        )
        tax = _xpath(
            root,
            "//ram:SpecifiedTradeSettlementHeaderMonetarySummation/ram:TaxTotalAmount/text()",
        )
        assert line_total == ["4500.00"]
        assert grand == ["4500.00"]
        assert tax == ["0.00"]


class TestCIIBuilderLines:
    def test_each_item_has_a_line_element(self) -> None:
        inv = _make_invoice_min()
        # ajoute une 2e ligne
        InvoiceItem.objects.create(
            invoice=inv,
            description="Hébergement 12 mois",
            quantity=Decimal("12"),
            unit_price=Decimal("50.00"),
            tax_rate=Decimal("0"),
            unit_code="MON",
            vat_category_code="E",
            vat_exemption_reason_code="VATEX-EU-79-C",
        )
        inv.compute_totals()
        root = etree.fromstring(build_cii_xml(inv))
        lines = _xpath(root, "//ram:IncludedSupplyChainTradeLineItem")
        assert len(lines) == 2

    def test_unit_code_passed_through(self) -> None:
        inv = _make_invoice_min()
        InvoiceItem.objects.create(
            invoice=inv,
            description="Heures consulting",
            quantity=Decimal("8"),
            unit_price=Decimal("125.00"),
            tax_rate=Decimal("0"),
            unit_code="HUR",
            vat_category_code="E",
            vat_exemption_reason_code="VATEX-EU-79-C",
        )
        inv.compute_totals()
        root = etree.fromstring(build_cii_xml(inv))
        units = _xpath(root, "//ram:BilledQuantity/@unitCode")
        assert "HUR" in units
