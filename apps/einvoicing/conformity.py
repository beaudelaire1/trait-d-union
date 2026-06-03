"""
Contrôleur de conformité — facturation électronique (EN 16931 / Factur-X).

Ce module prend en entrée un fichier de facture (PDF Factur-X hybride, ou XML
CII / UBL brut) et produit un rapport de conformité structuré, sans dépendre
d'une plateforme externe :

1. **Détection du format** : PDF/A-3 avec XML embarqué (Factur-X / ZUGFeRD),
   XML CII (UN/CEFACT) ou XML UBL (OASIS).
2. **Extraction du XML** : si PDF, on lit l'attachement `factur-x.xml`
   (ou variantes ZUGFeRD / XRechnung / Order-X) via pikepdf.
3. **Normalisation** : CII et UBL sont projetés sur un modèle commun
   ``InvoiceData`` (mêmes Business Terms BT-* EN 16931).
4. **Contrôles** : champs obligatoires (BG/BT), cohérence des totaux
   (BR-CO-10/13/14/15/16), TVA par catégorie, identifiants (SIREN/SIRET,
   TVA intra, IBAN) et indices PDF/A-3.

Le rapport est volontairement pédagogique : chaque contrôle porte son code
réglementaire (BT-1, BR-CO-15…), un statut (pass/fail/warn/info) et un message
en français clair. Aucun appel réseau, aucune donnée persistée.

Références :
- EN 16931-1 (modèle sémantique) + EN 16931 business rules (BR-*)
- Factur-X 1.0 (FNFE-MPE) — profils MINIMUM…EXTENDED
- ISO 19005-3 (PDF/A-3)
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Optional

from django.core.exceptions import ValidationError

from .validators import (
    validate_iban,
    validate_siren,
    validate_siret,
    validate_vat_intracom,
)

logger = logging.getLogger(__name__)

# Tolérance d'arrondi sur les contrôles arithmétiques (EN 16931 = 2 décimales).
EPSILON = Decimal("0.01")
MAX_FILE_BYTES = 15 * 1024 * 1024  # 15 Mo — garde-fou upload

# ── Namespaces ───────────────────────────────────────────────────────
NS_CII = {
    "rsm": "urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100",
    "ram": "urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100",
    "udt": "urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100",
}
NS_UBL = {
    "inv": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
    "cn": "urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2",
    "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
    "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
}

# Noms canoniques des XML embarqués reconnus dans un PDF (Factur-X & co).
EMBEDDED_XML_NAMES = (
    "factur-x.xml",
    "zugferd-invoice.xml",
    "ZUGFeRD-invoice.xml",
    "xrechnung.xml",
    "order-x.xml",
    "cii.xml",
)

# Profils Factur-X (URN → libellé lisible).
PROFILE_LABELS = {
    "urn:factur-x.eu:1p0:minimum": "MINIMUM",
    "urn:factur-x.eu:1p0:basicwl": "BASIC WL",
    "urn:cen.eu:en16931:2017#compliant#urn:factur-x.eu:1p0:basic": "BASIC",
    "urn:cen.eu:en16931:2017": "EN 16931 (COMFORT)",
    "urn:cen.eu:en16931:2017#conformant#urn:factur-x.eu:1p0:extended": "EXTENDED",
}

# Codes type de facture autorisés (UNTDID 1001, subset EN 16931 / FR).
INVOICE_TYPE_CODES = {"380", "381", "383", "384", "386", "389", "751", "326", "82"}

# Catégories TVA EN 16931 (UNTDID 5305).
VAT_CATEGORIES = {"S", "Z", "E", "AE", "K", "G", "O", "L", "M"}


# ─── Modèle commun ───────────────────────────────────────────────────
@dataclass
class InvoiceData:
    """Projection EN 16931 commune à CII et UBL."""

    syntax: str = ""              # "CII" | "UBL"
    profile_urn: Optional[str] = None
    business_process: Optional[str] = None
    number: Optional[str] = None             # BT-1
    type_code: Optional[str] = None          # BT-3
    issue_date: Optional[str] = None         # BT-2
    currency: Optional[str] = None           # BT-5

    seller_name: Optional[str] = None        # BT-27
    seller_country: Optional[str] = None     # BT-40
    seller_vat: Optional[str] = None         # BT-31
    seller_legal_id: Optional[str] = None    # BT-30

    buyer_name: Optional[str] = None         # BT-44
    buyer_country: Optional[str] = None      # BT-55
    buyer_vat: Optional[str] = None          # BT-48
    buyer_legal_id: Optional[str] = None     # BT-47

    payment_terms: Optional[str] = None      # BT-20
    due_date: Optional[str] = None           # BT-9
    iban: Optional[str] = None               # BT-84

    line_count: int = 0
    vat_breakdowns: list[dict] = field(default_factory=list)  # {category, rate, basis, amount}
    totals: dict = field(default_factory=dict)  # line, allowance, charge, tax_basis, tax_total, grand, prepaid, due


@dataclass
class CheckResult:
    code: str       # "BT-1", "BR-CO-15", "PDF/A-3"…
    label: str
    status: str     # "pass" | "fail" | "warn" | "info"
    detail: str = ""
    section: str = "structure"  # structure | identification | totaux | tva | format


@dataclass
class ConformityReport:
    filename: str = ""
    format_detected: str = "unknown"  # facturx_pdf | cii_xml | ubl_xml | pdf_no_xml | unknown
    syntax: str = ""                  # CII | UBL
    profile: Optional[str] = None
    checks: list[CheckResult] = field(default_factory=list)
    fatal_error: Optional[str] = None

    # ── Agrégats ──
    def add(self, code, label, status, detail="", section="structure"):
        self.checks.append(CheckResult(code, label, status, detail, section))

    @property
    def counts(self) -> dict:
        c = {"pass": 0, "fail": 0, "warn": 0, "info": 0}
        for chk in self.checks:
            c[chk.status] = c.get(chk.status, 0) + 1
        return c

    @property
    def score(self) -> int:
        """Score 0-100 : part des contrôles bloquants réussis, pénalisé par les warnings."""
        blocking = [c for c in self.checks if c.status in ("pass", "fail")]
        if not blocking:
            return 0
        passed = sum(1 for c in blocking if c.status == "pass")
        base = passed / len(blocking) * 100
        # Chaque warning retire 2 points (plafonné), sans descendre sous le ratio bloquant.
        warn_penalty = min(self.counts["warn"] * 2, 10)
        return max(0, int(round(base - warn_penalty)))

    @property
    def is_conformant(self) -> bool:
        return self.fatal_error is None and self.counts["fail"] == 0

    def to_json(self) -> dict:
        return {
            "filename": self.filename,
            "format_detected": self.format_detected,
            "syntax": self.syntax,
            "profile": self.profile,
            "is_conformant": self.is_conformant,
            "score": self.score,
            "counts": self.counts,
            "fatal_error": self.fatal_error,
            "checks": [
                {
                    "code": c.code,
                    "label": c.label,
                    "status": c.status,
                    "detail": c.detail,
                    "section": c.section,
                }
                for c in self.checks
            ],
        }


# ─── Point d'entrée ──────────────────────────────────────────────────
def check_invoice(content: bytes, filename: str = "") -> ConformityReport:
    """Analyse un fichier de facture et renvoie un ``ConformityReport``.

    ``content`` : octets bruts du fichier uploadé (PDF ou XML).
    ``filename`` : nom d'origine (sert à la détection + au rapport).
    """
    report = ConformityReport(filename=filename or "facture")

    if not content:
        report.fatal_error = "Fichier vide."
        return report
    if len(content) > MAX_FILE_BYTES:
        report.fatal_error = "Fichier trop volumineux (max 15 Mo)."
        return report

    is_pdf = content[:5] == b"%PDF-"
    xml_bytes: Optional[bytes] = None

    if is_pdf:
        xml_bytes, pdf_checks = _extract_xml_from_pdf(content, report)
        for chk in pdf_checks:
            report.checks.append(chk)
        if xml_bytes is None:
            report.format_detected = "pdf_no_xml"
            report.fatal_error = (
                "Aucun XML de facture n'est embarqué dans ce PDF. "
                "Un PDF imprimé ou scanné n'est pas une facture électronique : "
                "il faut un Factur-X (PDF/A-3 avec XML `factur-x.xml` attaché)."
            )
            return report
        report.format_detected = "facturx_pdf"
    else:
        # Suppose XML brut.
        xml_bytes = content
        report.format_detected = "xml"

    return _check_xml(xml_bytes, report)


# ─── Extraction PDF → XML ────────────────────────────────────────────
def _extract_xml_from_pdf(content: bytes, report: ConformityReport):
    """Extrait le XML embarqué + produit les contrôles PDF/A-3."""
    checks: list[CheckResult] = []
    xml_bytes: Optional[bytes] = None
    try:
        import pikepdf
    except ImportError:  # pragma: no cover
        return None, checks

    try:
        with pikepdf.open(io.BytesIO(content)) as pdf:
            # 1. Attachements
            attachments = dict(pdf.attachments) if hasattr(pdf, "attachments") else {}
            found_name = None
            for name in EMBEDDED_XML_NAMES:
                if name in attachments:
                    found_name = name
                    break
            # Fallback : n'importe quel .xml attaché.
            if not found_name:
                for key in attachments:
                    if str(key).lower().endswith(".xml"):
                        found_name = key
                        break

            if found_name:
                try:
                    filespec = attachments[found_name]
                    xml_bytes = filespec.get_file().read_bytes()
                except Exception:  # noqa: BLE001
                    try:
                        xml_bytes = bytes(attachments[found_name].obj["/EF"]["/F"].read_bytes())
                    except Exception:  # noqa: BLE001
                        xml_bytes = None
                checks.append(CheckResult(
                    "Factur-X", "XML de facture embarqué",
                    "pass" if xml_bytes else "fail",
                    f"Fichier attaché détecté : « {found_name} »." if xml_bytes
                    else "Attachement trouvé mais illisible.",
                    "format",
                ))
            else:
                checks.append(CheckResult(
                    "Factur-X", "XML de facture embarqué", "fail",
                    "Aucun fichier XML attaché au PDF.", "format",
                ))

            # 2. PDF/A-3 via XMP
            part = conformance = None
            try:
                with pdf.open_metadata() as meta:
                    part = meta.get("pdfaid:part")
                    conformance = meta.get("pdfaid:conformance")
            except Exception:  # noqa: BLE001
                pass
            if part:
                ok = str(part) == "3"
                checks.append(CheckResult(
                    "PDF/A-3", "Conformité PDF/A-3 (ISO 19005-3)",
                    "pass" if ok else "warn",
                    f"Déclaré PDF/A-{part}{conformance or ''}." if ok
                    else f"PDF/A-{part} déclaré : Factur-X exige la partie 3.",
                    "format",
                ))
            else:
                checks.append(CheckResult(
                    "PDF/A-3", "Conformité PDF/A-3 (ISO 19005-3)", "warn",
                    "Métadonnées XMP PDF/A absentes : le PDF risque d'être "
                    "refusé par un validateur veraPDF strict.",
                    "format",
                ))

            # 3. /AF (Associated Files) au niveau Catalog — clause 6.8 ISO 19005-3
            try:
                has_af = "/AF" in pdf.Root
            except Exception:  # noqa: BLE001
                has_af = False
            checks.append(CheckResult(
                "PDF/A-3 §6.8", "Fichier associé déclaré dans le Catalog (/AF)",
                "pass" if has_af else "warn",
                "Le XML est bien référencé comme fichier associé (/AF)." if has_af
                else "Entrée /AF manquante : certains validateurs refusent "
                     "l'association du XML au document.",
                "format",
            ))
    except Exception as exc:  # noqa: BLE001
        logger.warning("Lecture PDF échouée : %s", exc)
        checks.append(CheckResult(
            "PDF", "Lecture du PDF", "fail",
            "Le fichier PDF est illisible ou corrompu.", "format",
        ))

    return xml_bytes, checks


# ─── Parsing XML → InvoiceData ───────────────────────────────────────
def _check_xml(xml_bytes: bytes, report: ConformityReport) -> ConformityReport:
    from lxml import etree

    try:
        parser = etree.XMLParser(resolve_entities=False, no_network=True, huge_tree=False)
        root = etree.fromstring(xml_bytes, parser=parser)
    except Exception as exc:  # noqa: BLE001
        report.fatal_error = f"XML invalide : impossible de le parser ({exc})."
        return report

    tag = etree.QName(root).localname
    nsuri = etree.QName(root).namespace or ""

    if "CrossIndustryInvoice" in tag or NS_CII["rsm"] in nsuri:
        data = _parse_cii(root)
    elif tag in ("Invoice", "CreditNote") or "ubl" in nsuri:
        data = _parse_ubl(root, tag)
    else:
        report.fatal_error = (
            f"Format XML non reconnu (racine « {tag} »). "
            "Attendu : UN/CEFACT CII (Factur-X) ou OASIS UBL."
        )
        return report

    report.syntax = data.syntax
    if report.format_detected in ("xml", "unknown"):
        report.format_detected = "cii_xml" if data.syntax == "CII" else "ubl_xml"

    # Profil
    if data.profile_urn:
        report.profile = PROFILE_LABELS.get(data.profile_urn.strip(), data.profile_urn.strip())

    _run_checks(data, report)
    return report


def _txt(node) -> Optional[str]:
    if node is None:
        return None
    if isinstance(node, list):
        node = node[0] if node else None
        if node is None:
            return None
    val = node.text if hasattr(node, "text") else str(node)
    return val.strip() if val and val.strip() else None


def _parse_cii(root) -> InvoiceData:
    d = InvoiceData(syntax="CII")

    def find(path):
        return root.find(path, NS_CII)

    def findall(path):
        return root.findall(path, NS_CII)

    d.profile_urn = _txt(find(".//rsm:ExchangedDocumentContext/ram:GuidelineSpecifiedDocumentContextParameter/ram:ID"))
    d.business_process = _txt(find(".//rsm:ExchangedDocumentContext/ram:BusinessProcessSpecifiedDocumentContextParameter/ram:ID"))
    d.number = _txt(find(".//rsm:ExchangedDocument/ram:ID"))
    d.type_code = _txt(find(".//rsm:ExchangedDocument/ram:TypeCode"))
    d.issue_date = _txt(find(".//rsm:ExchangedDocument/ram:IssueDateTime/udt:DateTimeString"))

    agr = ".//rsm:SupplyChainTradeTransaction/ram:ApplicableHeaderTradeAgreement"
    d.seller_name = _txt(find(f"{agr}/ram:SellerTradeParty/ram:Name"))
    d.seller_country = _txt(find(f"{agr}/ram:SellerTradeParty/ram:PostalTradeAddress/ram:CountryID"))
    d.seller_legal_id = _txt(find(f"{agr}/ram:SellerTradeParty/ram:SpecifiedLegalOrganization/ram:ID"))
    for tax in findall(f"{agr}/ram:SellerTradeParty/ram:SpecifiedTaxRegistration/ram:ID"):
        if tax.get("schemeID") == "VA":
            d.seller_vat = _txt(tax)
    d.buyer_name = _txt(find(f"{agr}/ram:BuyerTradeParty/ram:Name"))
    d.buyer_country = _txt(find(f"{agr}/ram:BuyerTradeParty/ram:PostalTradeAddress/ram:CountryID"))
    d.buyer_legal_id = _txt(find(f"{agr}/ram:BuyerTradeParty/ram:SpecifiedLegalOrganization/ram:ID"))
    for tax in findall(f"{agr}/ram:BuyerTradeParty/ram:SpecifiedTaxRegistration/ram:ID"):
        if tax.get("schemeID") == "VA":
            d.buyer_vat = _txt(tax)

    settle = ".//rsm:SupplyChainTradeTransaction/ram:ApplicableHeaderTradeSettlement"
    d.currency = _txt(find(f"{settle}/ram:InvoiceCurrencyCode"))
    d.payment_terms = _txt(find(f"{settle}/ram:SpecifiedTradePaymentTerms/ram:Description"))
    d.due_date = _txt(find(f"{settle}/ram:SpecifiedTradePaymentTerms/ram:DueDateDateTime/udt:DateTimeString"))
    d.iban = _txt(find(f"{settle}/ram:SpecifiedTradeSettlementPaymentMeans/ram:PayeePartyCreditorFinancialAccount/ram:IBANID"))

    d.line_count = len(findall(".//ram:IncludedSupplyChainTradeLineItem"))

    for tax in findall(f"{settle}/ram:ApplicableTradeTax"):
        d.vat_breakdowns.append({
            "category": _txt(tax.find("ram:CategoryCode", NS_CII)),
            "rate": _txt(tax.find("ram:RateApplicablePercent", NS_CII)),
            "basis": _txt(tax.find("ram:BasisAmount", NS_CII)),
            "amount": _txt(tax.find("ram:CalculatedAmount", NS_CII)),
        })

    summ = f"{settle}/ram:SpecifiedTradeSettlementHeaderMonetarySummation"
    d.totals = {
        "line": _txt(find(f"{summ}/ram:LineTotalAmount")),
        "allowance": _txt(find(f"{summ}/ram:AllowanceTotalAmount")),
        "charge": _txt(find(f"{summ}/ram:ChargeTotalAmount")),
        "tax_basis": _txt(find(f"{summ}/ram:TaxBasisTotalAmount")),
        "tax_total": _txt(find(f"{summ}/ram:TaxTotalAmount")),
        "grand": _txt(find(f"{summ}/ram:GrandTotalAmount")),
        "prepaid": _txt(find(f"{summ}/ram:TotalPrepaidAmount")),
        "due": _txt(find(f"{summ}/ram:DuePayableAmount")),
    }
    return d


def _parse_ubl(root, tag) -> InvoiceData:
    d = InvoiceData(syntax="UBL")
    ns = NS_UBL

    def find(path):
        return root.find(path, ns)

    def findall(path):
        return root.findall(path, ns)

    d.profile_urn = _txt(find("cbc:CustomizationID"))
    d.business_process = _txt(find("cbc:ProfileID"))
    d.number = _txt(find("cbc:ID"))
    d.type_code = _txt(find("cbc:InvoiceTypeCode")) or _txt(find("cbc:CreditNoteTypeCode"))
    d.issue_date = _txt(find("cbc:IssueDate"))
    d.currency = _txt(find("cbc:DocumentCurrencyCode"))

    seller = "cac:AccountingSupplierParty/cac:Party"
    d.seller_name = _txt(find(f"{seller}/cac:PartyLegalEntity/cbc:RegistrationName")) or _txt(find(f"{seller}/cac:PartyName/cbc:Name"))
    d.seller_country = _txt(find(f"{seller}/cac:PostalAddress/cac:Country/cbc:IdentificationCode"))
    d.seller_vat = _txt(find(f"{seller}/cac:PartyTaxScheme/cbc:CompanyID"))
    d.seller_legal_id = _txt(find(f"{seller}/cac:PartyLegalEntity/cbc:CompanyID"))

    buyer = "cac:AccountingCustomerParty/cac:Party"
    d.buyer_name = _txt(find(f"{buyer}/cac:PartyLegalEntity/cbc:RegistrationName")) or _txt(find(f"{buyer}/cac:PartyName/cbc:Name"))
    d.buyer_country = _txt(find(f"{buyer}/cac:PostalAddress/cac:Country/cbc:IdentificationCode"))
    d.buyer_vat = _txt(find(f"{buyer}/cac:PartyTaxScheme/cbc:CompanyID"))
    d.buyer_legal_id = _txt(find(f"{buyer}/cac:PartyLegalEntity/cbc:CompanyID"))

    d.payment_terms = _txt(find("cac:PaymentTerms/cbc:Note"))
    d.due_date = _txt(find("cbc:DueDate")) or _txt(find("cac:PaymentMeans/cbc:PaymentDueDate"))
    d.iban = _txt(find("cac:PaymentMeans/cac:PayeeFinancialAccount/cbc:ID"))

    line_tag = "cac:InvoiceLine" if tag == "Invoice" else "cac:CreditNoteLine"
    d.line_count = len(findall(line_tag))

    for tax in findall("cac:TaxTotal/cac:TaxSubtotal"):
        cat = tax.find("cac:TaxCategory/cbc:ID", ns)
        d.vat_breakdowns.append({
            "category": _txt(cat),
            "rate": _txt(tax.find("cac:TaxCategory/cbc:Percent", ns)),
            "basis": _txt(tax.find("cbc:TaxableAmount", ns)),
            "amount": _txt(tax.find("cbc:TaxAmount", ns)),
        })

    lmt = "cac:LegalMonetaryTotal"
    d.totals = {
        "line": _txt(find(f"{lmt}/cbc:LineExtensionAmount")),
        "allowance": _txt(find(f"{lmt}/cbc:AllowanceTotalAmount")),
        "charge": _txt(find(f"{lmt}/cbc:ChargeTotalAmount")),
        "tax_basis": _txt(find(f"{lmt}/cbc:TaxExclusiveAmount")),
        "tax_total": _txt(find("cac:TaxTotal/cbc:TaxAmount")),
        "grand": _txt(find(f"{lmt}/cbc:TaxInclusiveAmount")),
        "prepaid": _txt(find(f"{lmt}/cbc:PrepaidAmount")),
        "due": _txt(find(f"{lmt}/cbc:PayableAmount")),
    }
    return d


# ─── Contrôles métier ────────────────────────────────────────────────
def _dec(value) -> Optional[Decimal]:
    if value is None or value == "":
        return None
    try:
        return Decimal(str(value).replace(",", "."))
    except (InvalidOperation, ValueError):
        return None


def _run_checks(d: InvoiceData, report: ConformityReport) -> None:
    # ── 1. Profil / syntaxe (BT-24) ──────────────────────────────────
    if d.profile_urn:
        known = d.profile_urn.strip() in PROFILE_LABELS
        report.add(
            "BT-24", "Identifiant de spécification (profil)",
            "pass" if known else "warn",
            f"Profil détecté : {report.profile}." if known
            else f"Profil non standard : « {d.profile_urn} ».",
            "structure",
        )
        if d.profile_urn.strip() == "urn:factur-x.eu:1p0:minimum":
            report.add(
                "Profil", "Niveau de profil", "warn",
                "Le profil MINIMUM ne porte pas les lignes ni assez de données "
                "pour être conforme EN 16931 — il sert surtout de e-reporting.",
                "structure",
            )
    else:
        report.add(
            "BT-24", "Identifiant de spécification (profil)", "fail",
            "Profil EN 16931 absent : document non identifiable comme facture "
            "électronique normalisée.",
            "structure",
        )

    # ── 2. Champs d'en-tête obligatoires ─────────────────────────────
    _require(report, "BT-1", "Numéro de facture", d.number, "structure")
    _require(report, "BT-2", "Date d'émission", d.issue_date, "structure")

    if d.type_code:
        ok = d.type_code in INVOICE_TYPE_CODES
        report.add(
            "BT-3", "Code type de facture (UNTDID 1001)",
            "pass" if ok else "warn",
            f"Code « {d.type_code} »." + ("" if ok else " — code peu courant, à vérifier."),
            "structure",
        )
    else:
        report.add("BT-3", "Code type de facture", "fail",
                   "Code type de document manquant.", "structure")

    if d.currency:
        ok = len(d.currency) == 3 and d.currency.isalpha()
        report.add("BT-5", "Devise de la facture",
                   "pass" if ok else "fail",
                   f"Devise « {d.currency} »." if ok else "Code devise invalide (ISO 4217 attendu).",
                   "structure")
    else:
        report.add("BT-5", "Devise de la facture", "fail",
                   "Devise manquante.", "structure")

    # ── 3. Vendeur / Acheteur ────────────────────────────────────────
    _require(report, "BT-27", "Nom du vendeur", d.seller_name, "identification")
    _require(report, "BT-40", "Pays du vendeur", d.seller_country, "identification")
    _require(report, "BT-44", "Nom de l'acheteur", d.buyer_name, "identification")
    _require(report, "BT-55", "Pays de l'acheteur", d.buyer_country, "identification")

    # SIREN/SIRET vendeur (BT-30)
    if d.seller_legal_id:
        _check_legal_id(report, "BT-30", "Identifiant légal vendeur", d.seller_legal_id)
    if d.buyer_legal_id:
        _check_legal_id(report, "BT-47", "Identifiant légal acheteur", d.buyer_legal_id)

    # TVA intra vendeur (BT-31)
    if d.seller_vat:
        _check_vat(report, "BT-31", "N° TVA intracom. vendeur", d.seller_vat)
    if d.buyer_vat:
        _check_vat(report, "BT-48", "N° TVA intracom. acheteur", d.buyer_vat)

    # ── 4. Lignes (EN 16931 / BASIC = ≥ 1 ligne) ─────────────────────
    profile_needs_lines = not (d.profile_urn and "minimum" in d.profile_urn.lower()) \
        and not (d.profile_urn and "basicwl" in d.profile_urn.lower())
    if profile_needs_lines:
        report.add(
            "BG-25", "Lignes de facture",
            "pass" if d.line_count > 0 else "fail",
            f"{d.line_count} ligne(s) détectée(s)." if d.line_count > 0
            else "Aucune ligne de facture : requis pour les profils BASIC et EN 16931.",
            "structure",
        )

    # ── 5. Conditions / échéance de paiement (BR-CO-25) ──────────────
    due = _dec(d.totals.get("due"))
    if due is not None and due > 0:
        has_terms = bool(d.due_date or d.payment_terms)
        report.add(
            "BR-CO-25", "Échéance ou conditions de paiement",
            "pass" if has_terms else "fail",
            "Échéance/conditions présentes." if has_terms
            else "Montant dû > 0 sans date d'échéance ni conditions de paiement.",
            "structure",
        )

    # ── 6. IBAN (BT-84) ──────────────────────────────────────────────
    if d.iban:
        try:
            validate_iban(d.iban)
            report.add("BT-84", "IBAN du compte de paiement", "pass",
                       "IBAN valide (clé ISO 13616).", "identification")
        except ValidationError as e:
            report.add("BT-84", "IBAN du compte de paiement", "fail",
                       _msg(e), "identification")

    # ── 7. TVA par catégorie (BG-23) ─────────────────────────────────
    if d.vat_breakdowns:
        report.add("BG-23", "Ventilation de la TVA", "pass",
                   f"{len(d.vat_breakdowns)} catégorie(s) de TVA déclarée(s).", "tva")
        for i, br in enumerate(d.vat_breakdowns, 1):
            _check_vat_breakdown(report, i, br)
    else:
        report.add("BG-23", "Ventilation de la TVA", "fail",
                   "Aucune ventilation de TVA : au moins une catégorie est exigée.", "tva")

    # ── 8. Cohérence des totaux ──────────────────────────────────────
    _check_totals(report, d)


def _require(report, code, label, value, section):
    report.add(
        code, label,
        "pass" if value else "fail",
        f"« {value} »" if value else "Champ obligatoire manquant.",
        section,
    )


def _msg(err: ValidationError) -> str:
    try:
        return " ".join(err.messages)
    except Exception:  # noqa: BLE001
        return str(err)


def _check_legal_id(report, code, label, value):
    digits = "".join(ch for ch in value if ch.isdigit())
    try:
        if len(digits) == 14:
            validate_siret(digits)
            report.add(code, label, "pass", f"SIRET valide ({digits}).", "identification")
        elif len(digits) == 9:
            validate_siren(digits)
            report.add(code, label, "pass", f"SIREN valide ({digits}).", "identification")
        else:
            report.add(code, label, "warn",
                       f"Identifiant « {value} » non reconnu comme SIREN/SIRET français.",
                       "identification")
    except ValidationError as e:
        report.add(code, label, "fail", _msg(e), "identification")


def _check_vat(report, code, label, value):
    try:
        validate_vat_intracom(value)
        report.add(code, label, "pass", f"Format valide ({value}).", "identification")
    except ValidationError as e:
        report.add(code, label, "fail", _msg(e), "identification")


def _check_vat_breakdown(report, idx, br):
    cat = br.get("category")
    rate = _dec(br.get("rate"))
    if not cat:
        report.add(f"BT-118.{idx}", f"Catégorie TVA (ligne {idx})", "fail",
                   "Code catégorie de TVA manquant.", "tva")
        return
    if cat not in VAT_CATEGORIES:
        report.add(f"BT-118.{idx}", f"Catégorie TVA (ligne {idx})", "warn",
                   f"Catégorie « {cat} » hors liste EN 16931 (UNTDID 5305).", "tva")
        return

    # BR-S-5 : catégorie S → taux > 0. BR-Z/E/O → taux 0.
    if cat == "S":
        ok = rate is not None and rate > 0
        report.add(f"BR-S-5.{idx}", f"Taux TVA standard (ligne {idx})",
                   "pass" if ok else "fail",
                   f"Catégorie S à {rate}%." if ok
                   else "Catégorie « S » (taux normal) sans taux > 0.", "tva")
    elif cat in ("Z", "E", "O", "AE", "K", "G"):
        ok = rate is None or rate == 0
        report.add(f"BR-{cat}.{idx}", f"Taux TVA catégorie {cat} (ligne {idx})",
                   "pass" if ok else "warn",
                   f"Catégorie {cat} à taux 0 — cohérent." if ok
                   else f"Catégorie {cat} devrait avoir un taux nul (trouvé {rate}%).", "tva")


def _check_totals(report, d: InvoiceData):
    t = d.totals
    line = _dec(t.get("line"))
    allowance = _dec(t.get("allowance")) or Decimal("0")
    charge = _dec(t.get("charge")) or Decimal("0")
    tax_basis = _dec(t.get("tax_basis"))
    tax_total = _dec(t.get("tax_total"))
    grand = _dec(t.get("grand"))
    prepaid = _dec(t.get("prepaid")) or Decimal("0")
    due = _dec(t.get("due"))

    # Présence des montants obligatoires (BT-106/109/112/115)
    _require(report, "BT-106", "Total net des lignes", t.get("line"), "totaux")
    _require(report, "BT-109", "Total HT (base imposable)", t.get("tax_basis"), "totaux")
    _require(report, "BT-112", "Total TTC", t.get("grand"), "totaux")
    _require(report, "BT-115", "Net à payer", t.get("due"), "totaux")

    # BR-CO-13 : BT-109 = BT-106 − BT-107 + BT-108
    if line is not None and tax_basis is not None:
        expected = line - allowance + charge
        ok = abs(expected - tax_basis) <= EPSILON
        report.add("BR-CO-13", "Base imposable = lignes − remises + charges",
                   "pass" if ok else "fail",
                   f"{tax_basis} = {line} − {allowance} + {charge}." if ok
                   else f"Incohérent : {tax_basis} ≠ {line} − {allowance} + {charge} (= {expected}).",
                   "totaux")

    # BR-CO-14 : BT-110 = Σ TVA par catégorie
    if tax_total is not None and d.vat_breakdowns:
        somme = sum((_dec(b.get("amount")) or Decimal("0")) for b in d.vat_breakdowns)
        ok = abs(somme - tax_total) <= EPSILON
        report.add("BR-CO-14", "Total TVA = somme des TVA par catégorie",
                   "pass" if ok else "fail",
                   f"Total TVA {tax_total} = Σ catégories ({somme})." if ok
                   else f"Incohérent : total TVA {tax_total} ≠ Σ catégories ({somme}).",
                   "totaux")

    # BR-CO-15 : BT-112 = BT-109 + BT-110
    if tax_basis is not None and tax_total is not None and grand is not None:
        expected = tax_basis + tax_total
        ok = abs(expected - grand) <= EPSILON
        report.add("BR-CO-15", "Total TTC = total HT + total TVA",
                   "pass" if ok else "fail",
                   f"{grand} = {tax_basis} + {tax_total}." if ok
                   else f"Incohérent : {grand} ≠ {tax_basis} + {tax_total} (= {expected}).",
                   "totaux")

    # BR-CO-16 : BT-115 = BT-112 − BT-113
    if grand is not None and due is not None:
        expected = grand - prepaid
        ok = abs(expected - due) <= EPSILON
        report.add("BR-CO-16", "Net à payer = total TTC − acomptes",
                   "pass" if ok else "fail",
                   f"{due} = {grand} − {prepaid}." if ok
                   else f"Incohérent : {due} ≠ {grand} − {prepaid} (= {expected}).",
                   "totaux")


__all__ = ["check_invoice", "ConformityReport", "CheckResult", "InvoiceData"]
