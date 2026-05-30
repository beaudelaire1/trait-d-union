"""
Builder XML UN/CEFACT CII (Cross Industry Invoice) — profil Factur-X.

Ce builder produit un XML conforme au standard EN 16931 dans la syntaxe
UN/CEFACT CII, embarquable dans un PDF/A-3 pour produire un Factur-X.

Profils supportés (FNFE-MPE / Factur-X 1.0+) :
- MINIMUM       : minimum (pas EN 16931 compliant)
- BASIC WL      : basic without lines (résumé)
- BASIC         : basic (compliant restreint)
- EN 16931      : profil complet recommandé France/Allemagne (par défaut TUS)
- EXTENDED      : profil étendu avec extensions sectorielles

Source de vérité : https://fnfe-mpe.org/factur-x/factur-x_en/

Auditabilité : chaque XML produit est validable par un outil tiers (ex.
KoSIT validator, validateur Chorus Pro, B2BRouter sandbox). Les BT-* (Business
Term) du modèle sémantique EN 16931 sont commentés pour faciliter la review.

Aucune dépendance autre que `lxml`. Pas de XSD compilée embarquée — la
conformité est obtenue par construction (tests + validation externe).
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING, Optional

from django.conf import settings
from lxml import etree

from ..codelists import LegalForm, TransactionType, VATPaymentBasis
from ..taxation import InvoiceTotals, compute_vat_breakdown

if TYPE_CHECKING:  # pragma: no cover
    from apps.factures.models import Invoice
    from apps.clients.models import ClientProfile


# ---------------------------------------------------------------------------
# Profils Factur-X — URN officiels (FNFE-MPE 1.0.07 et +)
# ---------------------------------------------------------------------------
FACTURX_PROFILES = {
    "MINIMUM":  "urn:factur-x.eu:1p0:minimum",
    "BASIC_WL": "urn:factur-x.eu:1p0:basicwl",
    "BASIC":    "urn:cen.eu:en16931:2017#compliant#urn:factur-x.eu:1p0:basic",
    "EN16931":  "urn:cen.eu:en16931:2017",
    "EXTENDED": "urn:cen.eu:en16931:2017#conformant#urn:factur-x.eu:1p0:extended",
}

# ---------------------------------------------------------------------------
# Namespaces XML CII
# ---------------------------------------------------------------------------
NS = {
    "rsm":  "urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100",
    "ram":  "urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100",
    "udt":  "urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100",
    "qdt":  "urn:un:unece:uncefact:data:standard:QualifiedDataType:100",
    "xsi":  "http://www.w3.org/2001/XMLSchema-instance",
}


def _q(tag: str) -> str:
    """Convertit `prefix:tag` en QName Clark notation."""
    prefix, local = tag.split(":", 1)
    return f"{{{NS[prefix]}}}{local}"


def _sub(parent, tag: str, text: Optional[str] = None, **attrs) -> etree._Element:
    el = etree.SubElement(parent, _q(tag), **{k: str(v) for k, v in attrs.items() if v is not None})
    if text is not None:
        el.text = str(text)
    return el


def _format_decimal(value: Decimal) -> str:
    """Format BT décimal : 2 décimales, point comme séparateur."""
    return f"{Decimal(value or 0):.2f}"


def _format_date(value: Optional[date]) -> str:
    return value.strftime("%Y%m%d") if value else ""


def _format_qty(value) -> str:
    return f"{Decimal(value or 0):.4f}"


def _normalize_iban(iban: str) -> str:
    """Normalise un IBAN selon BR-50 EN 16931 : majuscules, sans séparateur."""
    return "".join((iban or "").split()).replace("-", "").upper()


# ---------------------------------------------------------------------------
# Construction du document
# ---------------------------------------------------------------------------
def _emitter() -> dict:
    """Récupère les infos émetteur depuis settings.INVOICING['EMITTER']."""
    cfg = getattr(settings, "INVOICING", {}) or {}
    return cfg.get("EMITTER", {}) or {}


def _profile_urn(profile_key: Optional[str] = None) -> str:
    """Retourne l'URN du profil Factur-X cible."""
    cfg = getattr(settings, "INVOICING", {}) or {}
    key = (profile_key or cfg.get("FACTURX_PROFILE", "EN16931")).upper()
    return FACTURX_PROFILES.get(key, FACTURX_PROFILES["EN16931"])


def build_cii_xml(invoice: "Invoice", *, profile: Optional[str] = None) -> bytes:
    """Construit le XML CII (bytes) pour la facture donnée.

    Le XML est :
    - encodé UTF-8
    - pretty-printed (lisible par humain)
    - validable par construction sur les BT-* obligatoires du profil EN 16931
    """
    invoice.compute_totals()  # garantit cohérence des totaux affichés en PDF
    totals = compute_vat_breakdown(invoice)
    emitter = _emitter()

    nsmap = {None: NS["rsm"], "ram": NS["ram"], "udt": NS["udt"], "qdt": NS["qdt"], "xsi": NS["xsi"]}
    root = etree.Element(_q("rsm:CrossIndustryInvoice"), nsmap=nsmap)

    # =====================================================================
    # 1. ExchangedDocumentContext — profil Factur-X (BG-2 / BT-23, BT-24)
    # =====================================================================
    ctx = _sub(root, "rsm:ExchangedDocumentContext")
    business_ctx = _sub(ctx, "ram:BusinessProcessSpecifiedDocumentContextParameter")
    _sub(business_ctx, "ram:ID", _business_process(invoice))  # BT-23
    guideline_ctx = _sub(ctx, "ram:GuidelineSpecifiedDocumentContextParameter")
    _sub(guideline_ctx, "ram:ID", _profile_urn(profile))      # BT-24

    # =====================================================================
    # 2. ExchangedDocument — numéro, type, date, notes (BT-1, BT-3, BT-2, BT-22)
    # =====================================================================
    doc = _sub(root, "rsm:ExchangedDocument")
    _sub(doc, "ram:ID", invoice.number)                       # BT-1
    _sub(doc, "ram:TypeCode", invoice.invoice_type_code)      # BT-3
    issue_date_el = _sub(doc, "ram:IssueDateTime")
    _sub(issue_date_el, "udt:DateTimeString", _format_date(invoice.issue_date), format="102")  # BT-2
    if invoice.notes:
        note = _sub(doc, "ram:IncludedNote")
        _sub(note, "ram:Content", invoice.notes[:1000])

    # Mention légale TVA dérivée du régime configuré (jamais en dur)
    from ..legal import get_legal_tva_mention
    legal_mention = get_legal_tva_mention()
    if legal_mention:
        note = _sub(doc, "ram:IncludedNote")
        _sub(note, "ram:Content", legal_mention)
        _sub(note, "ram:SubjectCode", "TXD")

    # =====================================================================
    # 3. SupplyChainTradeTransaction — lignes + parties + paiement + totaux
    # =====================================================================
    trans = _sub(root, "rsm:SupplyChainTradeTransaction")

    # ---- 3.1 Lignes (BG-25, BG-26, BG-29, BG-30) ----------------------
    for idx, item in enumerate(invoice.invoice_items.all(), start=1):
        _build_line_item(trans, idx, item, invoice)

    # ---- 3.2 ApplicableHeaderTradeAgreement — Acheteur/Vendeur, refs ----
    agreement = _sub(trans, "ram:ApplicableHeaderTradeAgreement")
    if invoice.buyer_reference:
        _sub(agreement, "ram:BuyerReference", invoice.buyer_reference)  # BT-10

    seller = _sub(agreement, "ram:SellerTradeParty")
    _build_party(seller, _emitter_party(emitter), is_seller=True)

    buyer = _sub(agreement, "ram:BuyerTradeParty")
    _build_party(buyer, _client_party(invoice.client) if invoice.client else {})

    # ⚠️ ORDRE CII : SellerOrderReferencedDocument DOIT précéder
    # BuyerOrderReferencedDocument (séquence HeaderTradeAgreementType).
    # BT-14 — Sales order reference (devis accepté = ordre de vente).
    if getattr(invoice, "quote_id", None):
        seller_order = _sub(agreement, "ram:SellerOrderReferencedDocument")
        _sub(seller_order, "ram:IssuerAssignedID", invoice.quote.number)

    if invoice.purchase_order_ref:
        po = _sub(agreement, "ram:BuyerOrderReferencedDocument")
        _sub(po, "ram:IssuerAssignedID", invoice.purchase_order_ref)  # BT-13

    if invoice.contract_ref:
        ct = _sub(agreement, "ram:ContractReferencedDocument")
        _sub(ct, "ram:IssuerAssignedID", invoice.contract_ref)        # BT-12

    # ---- 3.3 ApplicableHeaderTradeDelivery — ⚠️ ne JAMAIS être vide
    # (règle BR-CII-31 : ActualDeliverySupplyChainEvent obligatoire en
    # profil EN 16931 ; on retombe sur la date d'émission si pas de date
    # de livraison fournie).
    delivery = _sub(trans, "ram:ApplicableHeaderTradeDelivery")
    if invoice.client and getattr(invoice.client, "has_distinct_delivery_address", False):
        ship_to = _sub(delivery, "ram:ShipToTradeParty")
        addr = invoice.client.effective_delivery_address
        _build_postal_address(_sub(ship_to, "ram:PostalTradeAddress"), addr)
    cse = _sub(delivery, "ram:ActualDeliverySupplyChainEvent")
    occ = _sub(cse, "ram:OccurrenceDateTime")
    delivery_date = invoice.delivery_date or invoice.issue_date
    _sub(occ, "udt:DateTimeString", _format_date(delivery_date), format="102")  # BT-72

    # ---- 3.4 ApplicableHeaderTradeSettlement — paiement, TVA, totaux ----
    settle = _sub(trans, "ram:ApplicableHeaderTradeSettlement")
    if emitter.get("iban"):
        _sub(settle, "ram:PaymentReference", invoice.number)
    _sub(settle, "ram:InvoiceCurrencyCode", invoice.currency_code or "EUR")  # BT-5

    # SpecifiedTradeSettlementPaymentMeans (BG-16 / BT-81)
    means = _sub(settle, "ram:SpecifiedTradeSettlementPaymentMeans")
    _sub(means, "ram:TypeCode", "30")  # 30 = virement (UNTDID 4461)
    if emitter.get("iban"):
        creditor = _sub(means, "ram:PayeePartyCreditorFinancialAccount")
        # BR-50 EN 16931 : IBAN sans espaces ni tirets, en majuscules.
        _sub(creditor, "ram:IBANID", _normalize_iban(emitter["iban"]))
        if emitter.get("bic"):
            inst = _sub(means, "ram:PayeeSpecifiedCreditorFinancialInstitution")
            _sub(inst, "ram:BICID", str(emitter["bic"]).replace(" ", "").upper())

    # ---- 3.5 ApplicableTradeTax — VAT breakdown (BG-23) ----
    for line in totals.breakdown:
        _build_tax_breakdown(settle, line)

    # ---- 3.6 BillingSpecifiedPeriod (période facturée) ----
    if invoice.delivery_period_start and invoice.delivery_period_end:
        period = _sub(settle, "ram:BillingSpecifiedPeriod")
        start = _sub(period, "ram:StartDateTime")
        _sub(start, "udt:DateTimeString", _format_date(invoice.delivery_period_start), format="102")
        end = _sub(period, "ram:EndDateTime")
        _sub(end, "udt:DateTimeString", _format_date(invoice.delivery_period_end), format="102")

    # ---- 3.7 SpecifiedTradePaymentTerms (BT-9 + BT-20) ----
    # ⚠️ Schematron BR-CO-25 : si DuePayableAmount > 0, alors au moins une
    # date d'échéance OU des conditions de paiement doivent être présentes.
    has_terms_content = bool(invoice.due_date or invoice.payment_terms)
    if has_terms_content or totals.payable_amount > 0:
        terms = _sub(settle, "ram:SpecifiedTradePaymentTerms")
        if invoice.payment_terms:
            _sub(terms, "ram:Description", invoice.payment_terms[:1000])
        else:
            # Description par défaut pour respecter BR-CO-25 sans imposer une
            # règle métier — on dérive de l'échéance si elle existe.
            default = (
                f"Paiement à réception de la facture, au plus tard le {invoice.due_date:%d/%m/%Y}."
                if invoice.due_date
                else "Paiement à réception de la facture."
            )
            _sub(terms, "ram:Description", default)
        if invoice.due_date:
            due = _sub(terms, "ram:DueDateDateTime")
            _sub(due, "udt:DateTimeString", _format_date(invoice.due_date), format="102")

    # ---- 3.8 SpecifiedTradeSettlementHeaderMonetarySummation (totaux) ----
    summary = _sub(settle, "ram:SpecifiedTradeSettlementHeaderMonetarySummation")
    _sub(summary, "ram:LineTotalAmount", _format_decimal(totals.line_net_total))      # BT-106
    if totals.charge_total > 0:
        _sub(summary, "ram:ChargeTotalAmount", _format_decimal(totals.charge_total))  # BT-108
    if totals.allowance_total > 0:
        _sub(summary, "ram:AllowanceTotalAmount", _format_decimal(totals.allowance_total))  # BT-107
    _sub(summary, "ram:TaxBasisTotalAmount", _format_decimal(totals.tax_basis_total))     # BT-109
    _sub(summary, "ram:TaxTotalAmount", _format_decimal(totals.tax_total),                # BT-110
         currencyID=invoice.currency_code or "EUR")
    _sub(summary, "ram:GrandTotalAmount", _format_decimal(totals.grand_total))            # BT-112
    _sub(summary, "ram:TotalPrepaidAmount", _format_decimal(totals.paid_amount))          # BT-113
    _sub(summary, "ram:DuePayableAmount", _format_decimal(totals.payable_amount))         # BT-115

    return etree.tostring(
        root,
        xml_declaration=True,
        encoding="UTF-8",
        pretty_print=True,
        standalone=False,
    )


# ---------------------------------------------------------------------------
# Helpers structurels
# ---------------------------------------------------------------------------
def _business_process(invoice: "Invoice") -> str:
    """Code processus métier (BT-23). Profil EN 16931 : `A1` par défaut.

    A1 = facture commerciale standard. Pour des cas spéciaux (avoir, acompte,
    refacturation), un mapping plus fin pourra être ajouté en Phase 3.
    """
    return "A1"


def _emitter_party(emitter: dict) -> dict:
    return {
        "id": emitter.get("siret") or emitter.get("siren") or "",
        "global_id": emitter.get("peppol_id") or "",
        "name": emitter.get("name") or "",
        "vat_intra": emitter.get("vat_intra") or "",
        "siren": emitter.get("siren") or "",
        "siret": emitter.get("siret") or "",
        "legal_form": emitter.get("legal_form") or "",
        "address_line": emitter.get("address_line") or "",
        "city": emitter.get("city") or "",
        "zip_code": emitter.get("zip_code") or "",
        "country_code": emitter.get("country_code") or "FR",
        "email": emitter.get("email") or "",
    }


def _client_party(client: "ClientProfile") -> dict:
    return {
        "id": client.siret or client.siren or "",
        "global_id": client.peppol_id or "",
        "name": client.company_name or client.full_name or client.email,
        "vat_intra": client.tva_number or "",
        "siren": client.siren or "",
        "siret": client.siret or "",
        "address_line": client.address_line or "",
        "city": client.city or "",
        "zip_code": client.zip_code or "",
        "country_code": client.country_code or "FR",
        "email": client.email or "",
    }


def _build_party(party_el: etree._Element, party: dict, *, is_seller: bool = False) -> None:
    """Construit un TradeParty (Seller ou Buyer).

    ⚠️ Ordre obligatoire de la séquence CII `TradePartyType` :
    ID → GlobalID → Name → SpecifiedLegalOrganization → PostalTradeAddress
    → URIUniversalCommunication → SpecifiedTaxRegistration.
    Toute permutation provoque un rejet XSD côté PA / Chorus Pro.
    """
    if not party:
        return

    if party.get("id"):
        _sub(party_el, "ram:ID", party["id"])  # BT-29 (alt) / BT-46 (alt)

    if party.get("global_id"):
        scheme, _, value = party["global_id"].partition(":")
        if value and scheme:
            _sub(party_el, "ram:GlobalID", value, schemeID=scheme)  # BT-29 / BT-46

    _sub(party_el, "ram:Name", party["name"] or "")  # BT-27 / BT-44

    # SpecifiedLegalOrganization — obligatoire si on a un SIREN, côté seller
    # comme côté buyer (BT-30 / BT-47). Le code 0002 est le scheme SIREN dans
    # la liste ICD/Peppol des identifiants d'organisation.
    if party.get("siren"):
        spec = _sub(party_el, "ram:SpecifiedLegalOrganization")
        _sub(spec, "ram:ID", party["siren"], schemeID="0002")
        if is_seller and party.get("legal_form_label"):
            _sub(spec, "ram:TradingBusinessName", party["legal_form_label"])

    addr_el = _sub(party_el, "ram:PostalTradeAddress")
    _build_postal_address(addr_el, party)

    if party.get("email"):
        comm = _sub(party_el, "ram:URIUniversalCommunication")
        _sub(comm, "ram:URIID", party["email"], schemeID="EM")

    if party.get("vat_intra"):
        tax = _sub(party_el, "ram:SpecifiedTaxRegistration")
        _sub(tax, "ram:ID", party["vat_intra"], schemeID="VA")


def _build_postal_address(addr_el: etree._Element, addr: dict) -> None:
    if addr.get("zip_code") or addr.get("zip"):
        _sub(addr_el, "ram:PostcodeCode", addr.get("zip_code") or addr.get("zip", ""))
    line = addr.get("address_line") or addr.get("line", "")
    if line:
        _sub(addr_el, "ram:LineOne", line)
    if addr.get("city"):
        _sub(addr_el, "ram:CityName", addr["city"])
    _sub(addr_el, "ram:CountryID", (addr.get("country_code") or addr.get("country") or "FR")[:2])


def _build_line_item(parent, line_id: int, item, invoice: "Invoice") -> None:
    """Construit un IncludedSupplyChainTradeLineItem (BG-25 / BG-26 / BG-29 / BG-30)."""
    line = _sub(parent, "ram:IncludedSupplyChainTradeLineItem")

    # BG-25 LineID
    doc_line = _sub(line, "ram:AssociatedDocumentLineDocument")
    _sub(doc_line, "ram:LineID", str(line_id))

    # BG-31 Item information (BT-153, BT-155)
    product = _sub(line, "ram:SpecifiedTradeProduct")
    if getattr(item, "item_identifier", ""):
        _sub(product, "ram:SellerAssignedID", item.item_identifier)  # BT-155
    _sub(product, "ram:Name", item.description or "Article")          # BT-153

    # BG-29 Price details (BT-146)
    price_block = _sub(line, "ram:SpecifiedLineTradeAgreement")
    net_price = _sub(price_block, "ram:NetPriceProductTradePrice")
    _sub(net_price, "ram:ChargeAmount", _format_decimal(Decimal(item.unit_price or 0)))

    # BG-26 Delivery (BT-129 quantity)
    delivery = _sub(line, "ram:SpecifiedLineTradeDelivery")
    _sub(delivery, "ram:BilledQuantity", _format_qty(item.quantity),
         unitCode=getattr(item, "unit_code", None) or "C62")

    # BG-30 Settlement (taxes + totals)
    settle = _sub(line, "ram:SpecifiedLineTradeSettlement")
    tax = _sub(settle, "ram:ApplicableTradeTax")
    _sub(tax, "ram:TypeCode", "VAT")
    cat = (getattr(item, "vat_category_code", "") or "E").upper()
    reason = getattr(item, "vat_exemption_reason_code", "") or ""
    if reason and cat in {"E", "K", "AE", "G", "O", "Z"}:
        _sub(tax, "ram:ExemptionReason", reason)  # BT-120
    _sub(tax, "ram:CategoryCode", cat)             # BT-151
    # BR-O-5 : pas de RateApplicablePercent quand la catégorie est "O".
    if cat != "O":
        _sub(tax, "ram:RateApplicablePercent", _format_decimal(Decimal(item.tax_rate or 0)))  # BT-152

    line_total = Decimal(item.total_ht or 0)
    summation = _sub(settle, "ram:SpecifiedTradeSettlementLineMonetarySummation")
    _sub(summation, "ram:LineTotalAmount", _format_decimal(line_total))  # BT-131


def _build_tax_breakdown(settle_el, line) -> None:
    """Construit BG-23 (VAT Breakdown) pour une catégorie/taux donné.

    ⚠️ Schematron EN 16931 :
    - BR-O-5/6 : pour la catégorie ``O`` (hors champ TVA), ``RateApplicablePercent``
      ne doit PAS être présent.
    - BR-E-5/6 et BR-Z-5/6 : pour ``E`` (exonéré, franchise) et ``Z`` (taux 0),
      le taux doit être 0 et le ``ExemptionReason`` est obligatoire pour ``E``.
    Émettre ``0.00`` sur la catégorie ``O`` provoque un rejet Schematron sur la
    plupart des plateformes (Chorus Pro, IOPOLE, KoSIT).
    """
    cat = (line.category_code or "").upper()
    tax = _sub(settle_el, "ram:ApplicableTradeTax")
    _sub(tax, "ram:CalculatedAmount", _format_decimal(line.tax_amount))    # BT-117
    _sub(tax, "ram:TypeCode", "VAT")
    if line.exemption_reason_code and cat in {"E", "K", "AE", "G", "O", "Z"}:
        _sub(tax, "ram:ExemptionReason", line.exemption_reason_code)        # BT-120
    _sub(tax, "ram:BasisAmount", _format_decimal(line.taxable_amount))      # BT-116
    _sub(tax, "ram:CategoryCode", cat or "S")                               # BT-118
    if line.exemption_reason_code:
        _sub(tax, "ram:ExemptionReasonCode", line.exemption_reason_code)    # BT-121
    # BT-119 : RateApplicablePercent obligatoire pour S, ZERO pour Z, ABSENT pour O.
    if cat != "O":
        _sub(tax, "ram:RateApplicablePercent", _format_decimal(line.rate_percent))


__all__ = ["build_cii_xml", "FACTURX_PROFILES"]
