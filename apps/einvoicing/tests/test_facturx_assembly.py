"""Tests d'assemblage Factur-X (PDF/A-3 + XML CII embarqué).

Pour rester rapide et indépendant de WeasyPrint, on génère un PDF minimal
avec pikepdf et on vérifie que :
- le XML est attaché sous le nom canonique `factur-x.xml`
- les métadonnées XMP contiennent les marqueurs PDF/A-3 et Factur-X
- la relation Adobe (AFRelationship) est posée
"""

from __future__ import annotations

from decimal import Decimal
from io import BytesIO

import pikepdf
import pytest

from apps.clients.models import ClientProfile
from apps.einvoicing.builders.facturx import (
    FACTURX_FILENAME,
    FacturXAttachmentRelationship,
    build_facturx_pdf,
)
from apps.factures.models import Invoice, InvoiceItem


pytestmark = pytest.mark.django_db


def _make_minimal_pdf() -> bytes:
    """Crée un PDF vierge en mémoire (1 page A4)."""
    buf = BytesIO()
    pdf = pikepdf.Pdf.new()
    # une page vide A4 : pikepdf >= 8 expose Pdf.add_blank_page
    pdf.add_blank_page(page_size=(595, 842))
    pdf.save(buf)
    return buf.getvalue()


def _make_invoice() -> Invoice:
    client = ClientProfile.objects.create(
        full_name="Acme SARL",
        email="acme@example.com",
        is_business=True,
        siren="908264112",
        country_code="FR",
    )
    inv = Invoice.objects.create(client=client)
    InvoiceItem.objects.create(
        invoice=inv,
        description="Service",
        quantity=Decimal("1"),
        unit_price=Decimal("1000.00"),
        tax_rate=Decimal("0"),
        vat_category_code="E",
        vat_exemption_reason_code="VATEX-EU-79-C",
    )
    inv.compute_totals()
    return inv


class TestFacturXAssembly:
    def test_xml_is_attached_under_canonical_name(self) -> None:
        inv = _make_invoice()
        result = build_facturx_pdf(inv, pdf_bytes=_make_minimal_pdf())
        with pikepdf.open(BytesIO(result)) as pdf:
            assert FACTURX_FILENAME in pdf.attachments
            spec = pdf.attachments[FACTURX_FILENAME]
            payload = spec.get_file().read_bytes()
            assert payload.startswith(b"<?xml")
            assert b"CrossIndustryInvoice" in payload

    def test_af_relationship_is_alternative(self) -> None:
        inv = _make_invoice()
        result = build_facturx_pdf(
            inv,
            pdf_bytes=_make_minimal_pdf(),
            relationship=FacturXAttachmentRelationship.ALTERNATIVE,
        )
        with pikepdf.open(BytesIO(result)) as pdf:
            spec = pdf.attachments[FACTURX_FILENAME].obj
            af = spec.get("/AFRelationship")
            assert af is not None
            assert str(af) == "/Alternative"

    def test_xmp_metadata_contains_facturx_markers(self) -> None:
        inv = _make_invoice()
        result = build_facturx_pdf(inv, pdf_bytes=_make_minimal_pdf())
        with pikepdf.open(BytesIO(result)) as pdf:
            metadata_obj = pdf.Root.get("/Metadata")
            assert metadata_obj is not None
            xmp = bytes(metadata_obj.read_bytes())
            assert b"pdfaid:part>3" in xmp
            assert b"factur-x" in xmp.lower()
            assert b"DocumentType>INVOICE" in xmp


class TestFacturXIdempotence:
    def test_double_attach_does_not_corrupt(self) -> None:
        """Reconstruire un Factur-X à partir d'un Factur-X existant doit toujours
        contenir un seul attachement nommé `factur-x.xml`."""
        inv = _make_invoice()
        first = build_facturx_pdf(inv, pdf_bytes=_make_minimal_pdf())
        second = build_facturx_pdf(inv, pdf_bytes=first)
        with pikepdf.open(BytesIO(second)) as pdf:
            attachments = list(pdf.attachments.keys())
            assert attachments.count(FACTURX_FILENAME) == 1
