"""Tests du contrôleur de conformité facture électronique (EN 16931)."""

from __future__ import annotations

import pytest

from apps.einvoicing.conformity import check_invoice


# ── XML CII minimal mais cohérent ────────────────────────────────────
def _cii_xml(*, grand="120.00", tax="20.00", basis="100.00", line="100.00",
             due="120.00", cat="S", rate="20", buyer_siren="552081317") -> bytes:
    """SIREN 552081317 (Danone) = clé Luhn valide ; sert d'acheteur réaliste."""
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rsm:CrossIndustryInvoice
  xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100"
  xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100"
  xmlns:udt="urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100">
  <rsm:ExchangedDocumentContext>
    <ram:GuidelineSpecifiedDocumentContextParameter>
      <ram:ID>urn:cen.eu:en16931:2017</ram:ID>
    </ram:GuidelineSpecifiedDocumentContextParameter>
  </rsm:ExchangedDocumentContext>
  <rsm:ExchangedDocument>
    <ram:ID>FAC-TEST-001</ram:ID>
    <ram:TypeCode>380</ram:TypeCode>
    <ram:IssueDateTime><udt:DateTimeString format="102">20260101</udt:DateTimeString></ram:IssueDateTime>
  </rsm:ExchangedDocument>
  <rsm:SupplyChainTradeTransaction>
    <ram:IncludedSupplyChainTradeLineItem/>
    <ram:ApplicableHeaderTradeAgreement>
      <ram:SellerTradeParty>
        <ram:Name>Trait d'Union Studio</ram:Name>
        <ram:SpecifiedLegalOrganization><ram:ID schemeID="0002">908264112</ram:ID></ram:SpecifiedLegalOrganization>
        <ram:PostalTradeAddress><ram:CountryID>FR</ram:CountryID></ram:PostalTradeAddress>
      </ram:SellerTradeParty>
      <ram:BuyerTradeParty>
        <ram:Name>Client Test SARL</ram:Name>
        <ram:SpecifiedLegalOrganization><ram:ID schemeID="0002">{buyer_siren}</ram:ID></ram:SpecifiedLegalOrganization>
        <ram:PostalTradeAddress><ram:CountryID>FR</ram:CountryID></ram:PostalTradeAddress>
      </ram:BuyerTradeParty>
    </ram:ApplicableHeaderTradeAgreement>
    <ram:ApplicableHeaderTradeDelivery/>
    <ram:ApplicableHeaderTradeSettlement>
      <ram:InvoiceCurrencyCode>EUR</ram:InvoiceCurrencyCode>
      <ram:ApplicableTradeTax>
        <ram:CalculatedAmount>{tax}</ram:CalculatedAmount>
        <ram:CategoryCode>{cat}</ram:CategoryCode>
        <ram:BasisAmount>{basis}</ram:BasisAmount>
        <ram:RateApplicablePercent>{rate}</ram:RateApplicablePercent>
      </ram:ApplicableTradeTax>
      <ram:SpecifiedTradePaymentTerms>
        <ram:Description>Paiement à 30 jours.</ram:Description>
      </ram:SpecifiedTradePaymentTerms>
      <ram:SpecifiedTradeSettlementHeaderMonetarySummation>
        <ram:LineTotalAmount>{line}</ram:LineTotalAmount>
        <ram:TaxBasisTotalAmount>{basis}</ram:TaxBasisTotalAmount>
        <ram:TaxTotalAmount currencyID="EUR">{tax}</ram:TaxTotalAmount>
        <ram:GrandTotalAmount>{grand}</ram:GrandTotalAmount>
        <ram:DuePayableAmount>{due}</ram:DuePayableAmount>
      </ram:SpecifiedTradeSettlementHeaderMonetarySummation>
    </ram:ApplicableHeaderTradeSettlement>
  </rsm:SupplyChainTradeTransaction>
</rsm:CrossIndustryInvoice>""".encode("utf-8")


class TestCIIConformity:
    def test_valid_invoice_is_conformant(self):
        report = check_invoice(_cii_xml(), "test.xml")
        assert report.fatal_error is None
        assert report.syntax == "CII"
        assert report.format_detected == "cii_xml"
        assert report.is_conformant, [c for c in report.checks if c.status == "fail"]
        assert report.score == 100

    def test_profile_detected(self):
        report = check_invoice(_cii_xml(), "test.xml")
        assert report.profile == "EN 16931 (COMFORT)"

    def test_totals_incoherence_flagged(self):
        # grand = 999 ≠ basis + tax → BR-CO-15 doit échouer
        report = check_invoice(_cii_xml(grand="999.00"), "test.xml")
        codes = {c.code: c.status for c in report.checks}
        assert codes.get("BR-CO-15") == "fail"
        assert not report.is_conformant

    def test_vat_total_mismatch_flagged(self):
        report = check_invoice(_cii_xml(tax="20.00", grand="120.00"), "test.xml")
        # cohérent ici ; on vérifie le contraire avec une TVA décalée
        report2 = check_invoice(_cii_xml(tax="20.00", basis="100.00",
                                         grand="120.00", due="120.00", rate="20"), "test.xml")
        assert any(c.code == "BR-CO-14" for c in report2.checks)

    def test_invalid_buyer_siren_flagged(self):
        # SIREN privé (préfixe 3-9) avec mauvaise clé Luhn → doit échouer.
        # Les préfixes 1 et 2 sont reserves aux administrations / collectivites
        # et echappent au controle Luhn (regle INSEE).
        report = check_invoice(_cii_xml(buyer_siren="987654321"), "test.xml")
        bt47 = [c for c in report.checks if c.code == "BT-47"]
        assert bt47 and bt47[0].status == "fail"

    def test_public_sector_siren_accepted_without_luhn(self):
        # Mairie de Cayenne : 218000037 — SIREN de collectivite (prefixe 2),
        # hors regle Luhn par convention INSEE. Doit etre accepte.
        report = check_invoice(_cii_xml(buyer_siren="218000037"), "test.xml")
        bt47 = [c for c in report.checks if c.code == "BT-47"]
        assert bt47 and bt47[0].status == "pass"
        assert report.is_conformant

    def test_missing_number_flagged(self):
        xml = _cii_xml().replace(b"<ram:ID>FAC-TEST-001</ram:ID>", b"<ram:ID></ram:ID>")
        report = check_invoice(xml, "test.xml")
        bt1 = [c for c in report.checks if c.code == "BT-1"]
        assert bt1 and bt1[0].status == "fail"


class TestFormatDetection:
    def test_unknown_xml_root(self):
        report = check_invoice(b"<?xml version='1.0'?><Foo/>", "x.xml")
        assert report.fatal_error is not None

    def test_garbage_not_xml(self):
        report = check_invoice(b"not xml at all", "x.xml")
        assert report.fatal_error is not None

    def test_empty_file(self):
        report = check_invoice(b"", "x.xml")
        assert report.fatal_error == "Fichier vide."

    def test_pdf_without_xml(self):
        # PDF minimal valide sans attachement → pdf_no_xml
        minimal_pdf = b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF"
        report = check_invoice(minimal_pdf, "scan.pdf")
        assert report.format_detected == "pdf_no_xml"
        assert report.fatal_error is not None


class TestUBLConformity:
    def _ubl(self) -> bytes:
        return """<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
  xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
  xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2">
  <cbc:CustomizationID>urn:cen.eu:en16931:2017</cbc:CustomizationID>
  <cbc:ID>UBL-001</cbc:ID>
  <cbc:IssueDate>2026-01-01</cbc:IssueDate>
  <cbc:DueDate>2026-01-31</cbc:DueDate>
  <cbc:InvoiceTypeCode>380</cbc:InvoiceTypeCode>
  <cbc:DocumentCurrencyCode>EUR</cbc:DocumentCurrencyCode>
  <cac:AccountingSupplierParty><cac:Party>
    <cac:PartyLegalEntity><cbc:RegistrationName>Vendeur SAS</cbc:RegistrationName></cac:PartyLegalEntity>
    <cac:PostalAddress><cac:Country><cbc:IdentificationCode>FR</cbc:IdentificationCode></cac:Country></cac:PostalAddress>
  </cac:Party></cac:AccountingSupplierParty>
  <cac:AccountingCustomerParty><cac:Party>
    <cac:PartyLegalEntity><cbc:RegistrationName>Acheteur SARL</cbc:RegistrationName></cac:PartyLegalEntity>
    <cac:PostalAddress><cac:Country><cbc:IdentificationCode>FR</cbc:IdentificationCode></cac:Country></cac:PostalAddress>
  </cac:Party></cac:AccountingCustomerParty>
  <cac:InvoiceLine><cbc:ID>1</cbc:ID></cac:InvoiceLine>
  <cac:TaxTotal>
    <cbc:TaxAmount>20.00</cbc:TaxAmount>
    <cac:TaxSubtotal>
      <cbc:TaxableAmount>100.00</cbc:TaxableAmount>
      <cbc:TaxAmount>20.00</cbc:TaxAmount>
      <cac:TaxCategory><cbc:ID>S</cbc:ID><cbc:Percent>20</cbc:Percent></cac:TaxCategory>
    </cac:TaxSubtotal>
  </cac:TaxTotal>
  <cac:LegalMonetaryTotal>
    <cbc:LineExtensionAmount>100.00</cbc:LineExtensionAmount>
    <cbc:TaxExclusiveAmount>100.00</cbc:TaxExclusiveAmount>
    <cbc:TaxInclusiveAmount>120.00</cbc:TaxInclusiveAmount>
    <cbc:PayableAmount>120.00</cbc:PayableAmount>
  </cac:LegalMonetaryTotal>
</Invoice>""".encode("utf-8")

    def test_valid_ubl(self):
        report = check_invoice(self._ubl(), "ubl.xml")
        assert report.syntax == "UBL"
        assert report.format_detected == "ubl_xml"
        assert report.is_conformant, [c for c in report.checks if c.status == "fail"]


class TestPdfExtractionFallback:
    """L'extraction doit retrouver le XML même si l'attachement est exclusivement
    declare via /AF (Associated Files) au niveau Catalog, sans entree dans
    /Names/EmbeddedFiles. Cas frequent des PDF re-emballes ou produits par
    des outils qui s'ecartent de la pratique Adobe."""

    def test_xml_extracted_from_af_only(self, tmp_path):
        import io
        import pikepdf

        xml = _cii_xml()

        # PDF minimal viable + attachement via AttachedFileSpec puis on
        # supprime l'entree /Names/EmbeddedFiles pour simuler le cas reel.
        pdf = pikepdf.Pdf.new()
        pdf.add_blank_page(page_size=(595, 842))
        fs = pikepdf.AttachedFileSpec(pdf, xml, mime_type="application/xml")
        pdf.attachments["factur-x.xml"] = fs
        af_obj = pdf.attachments["factur-x.xml"].obj
        af_obj["/AFRelationship"] = pikepdf.Name("/Alternative")
        pdf.Root["/AF"] = pikepdf.Array([pdf.make_indirect(af_obj)])
        # On retire l'entree /Names → pikepdf.attachments sera vide,
        # seul /AF référencera le filespec.
        try:
            del pdf.Root["/Names"]
        except (KeyError, AttributeError):
            pass

        buf = io.BytesIO()
        pdf.save(buf)
        data = buf.getvalue()

        report = check_invoice(data, "af-only.pdf")
        assert report.format_detected == "facturx_pdf"
        assert report.fatal_error is None
        assert report.syntax == "CII"
        assert report.counts["pass"] > 0
