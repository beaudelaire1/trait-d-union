"""
Code lists réglementaires pour la facturation électronique européenne.

Aucune chaîne réglementée ne doit être écrite "en dur" ailleurs dans le code.
Source de vérité unique pour :

- VAT_CATEGORY_CODES   : UNTDID 5305 (catégories TVA EN 16931 / Factur-X)
- VATEX_REASON_CODES   : motifs d'exemption EN 16931 (CEF eInvoicing)
- UN_UNIT_CODES        : codes d'unité UN/ECE Recommendation 20 (subset utile)
- TRANSACTION_TYPES    : nature de transaction (réforme FR 2026)
- VAT_PAYMENT_BASIS    : base de paiement TVA (débits / encaissements)
- INVOICE_TYPE_CODES   : UNTDID 1001 (subset utile pour FR)
- LIFECYCLE_STATES     : états du cycle de vie d'une facture côté PDP

Ces listes sont également exposées en `choices` Django pour les modèles.

Références :
- EN 16931 / CEF eInvoicing code lists
- UN/ECE Recommendation 20 (units of measure)
- Service-public.fr — mentions obligatoires de la facture
"""

from __future__ import annotations

from django.db import models
from django.utils.translation import gettext_lazy as _


# ---------------------------------------------------------------------------
# VAT category codes (UNTDID 5305) — sous-ensemble pertinent EN 16931
# ---------------------------------------------------------------------------
class VATCategory(models.TextChoices):
    STANDARD = "S", _("Standard rate (taux normal)")
    ZERO = "Z", _("Zero rated goods (taux zéro)")
    EXEMPT = "E", _("Exempt from tax (exonéré, ex. franchise en base)")
    REVERSE_CHARGE = "AE", _("VAT Reverse Charge (autoliquidation)")
    INTRA_EU = "K", _("VAT exempt for EEA intra-community supply")
    EXPORT_OUTSIDE_EU = "G", _("Free export item, VAT not charged (export hors UE)")
    OUT_OF_SCOPE = "O", _("Services outside scope of tax (hors champ)")
    CANARY_ISLANDS = "L", _("Canary Islands general indirect tax")
    CEUTA_MELILLA = "M", _("Tax for production, services and importation in Ceuta and Melilla")


# ---------------------------------------------------------------------------
# VATEX reason codes — motifs d'exemption EN 16931
# Liste raccourcie au strict utile pour TUS + scénarios fréquents FR.
# Le code complet est maintenu par Connecting Europe Facility (CEF).
# ---------------------------------------------------------------------------
VATEX_REASON_CODES: dict[str, str] = {
    # Article 79c — franchise en base TVA (cas TUS)
    "VATEX-EU-79-C": "Franchise en base de TVA (art. 293 B du CGI / art. 79c directive 2006/112/CE)",
    # Autoliquidation
    "VATEX-EU-AE": "Reverse charge — autoliquidation par le preneur",
    # Livraison intracommunautaire
    "VATEX-EU-IC": "Intra-community supply — livraison intracommunautaire (art. 138)",
    # Export hors UE
    "VATEX-EU-G": "Export outside the EU — exportation hors UE (art. 146)",
    # Article 132 — exemptions d'intérêt général (santé, éducation, culture, etc.)
    "VATEX-EU-132": "Exemption art. 132 directive 2006/112/CE",
    "VATEX-EU-132-1A": "Services postaux publics (art. 132.1.a)",
    "VATEX-EU-132-1B": "Hospitalisation et soins médicaux (art. 132.1.b)",
    "VATEX-EU-132-1C": "Prestations de soins par professions médicales (art. 132.1.c)",
    "VATEX-EU-132-1I": "Éducation (art. 132.1.i)",
    "VATEX-EU-132-1J": "Cours particuliers (art. 132.1.j)",
    # Article 143 — importations exonérées
    "VATEX-EU-143": "Importations exonérées (art. 143)",
    # Article 148 — opérations maritimes/aériennes
    "VATEX-EU-148": "Opérations maritimes / aériennes (art. 148)",
    # Article 151 — relations diplomatiques
    "VATEX-EU-151": "Relations diplomatiques (art. 151)",
    # Hors champ
    "VATEX-EU-O": "Outside the scope of VAT — hors champ d'application TVA",
}


def vatex_choices() -> list[tuple[str, str]]:
    """Retourne les codes VATEX au format Django choices."""
    return list(VATEX_REASON_CODES.items())


# ---------------------------------------------------------------------------
# UN/ECE Recommendation 20 — codes d'unité utiles pour TUS
# ---------------------------------------------------------------------------
UN_UNIT_CODES: dict[str, str] = {
    "C62": "One (unité, sans dimension)",
    "EA": "Each (chaque)",
    "LS": "Lump sum (forfait)",
    "HUR": "Hour (heure)",
    "MIN": "Minute",
    "DAY": "Day (jour)",
    "WEE": "Week (semaine)",
    "MON": "Month (mois)",
    "ANN": "Year (année)",
    "MTR": "Metre (mètre)",
    "MTK": "Square metre (m²)",
    "MTQ": "Cubic metre (m³)",
    "KGM": "Kilogram (kilogramme)",
    "GRM": "Gram (gramme)",
    "TNE": "Tonne (tonne métrique)",
    "LTR": "Litre",
    "PCE": "Piece (pièce)",
    "SET": "Set (jeu)",
    "P1": "Percent (pourcent)",
    "MGM": "Megabyte",
    "GB": "Gigabyte",
    "KWH": "Kilowatt hour",
}


def unit_code_choices() -> list[tuple[str, str]]:
    """Retourne les codes d'unité au format Django choices."""
    return list(UN_UNIT_CODES.items())


# ---------------------------------------------------------------------------
# Type de transaction (réforme française 2026)
# ---------------------------------------------------------------------------
class TransactionType(models.TextChoices):
    GOODS = "GOODS", _("Livraison de biens")
    SERVICES = "SERVICES", _("Prestation de services")
    MIXED = "MIXED", _("Mixte (biens + services)")


# ---------------------------------------------------------------------------
# Base de paiement TVA (FR)
# - DEBITS    : TVA exigible à l'émission de la facture (livraison de biens)
# - RECEIPTS  : TVA exigible à l'encaissement (prestations de services par défaut)
# ---------------------------------------------------------------------------
class VATPaymentBasis(models.TextChoices):
    DEBITS = "DEBITS", _("TVA d'après les débits")
    RECEIPTS = "RECEIPTS", _("TVA d'après les encaissements")
    NOT_APPLICABLE = "NA", _("Non applicable (franchise / exonération)")


# ---------------------------------------------------------------------------
# Invoice type code (UNTDID 1001) — subset utile pour FR/EN16931
# ---------------------------------------------------------------------------
class InvoiceTypeCode(models.TextChoices):
    COMMERCIAL_INVOICE = "380", _("Commercial invoice (facture commerciale)")
    CREDIT_NOTE = "381", _("Credit note (avoir)")
    DEBIT_NOTE = "383", _("Debit note (note de débit)")
    CORRECTED_INVOICE = "384", _("Corrected invoice (facture rectificative)")
    SELF_BILLED_INVOICE = "389", _("Self-billed invoice (autofacturation)")
    PREPAYMENT_INVOICE = "386", _("Prepayment invoice (facture d'acompte)")


# ---------------------------------------------------------------------------
# Lifecycle states côté PDP (états de cycle de vie d'une facture)
# Source : XP Z12-013 + retours d'expérience Chorus Pro / B2BRouter
# ---------------------------------------------------------------------------
class LifecycleState(models.TextChoices):
    DRAFT = "DRAFT", _("Brouillon (non soumise)")
    SUBMITTED = "SUBMITTED", _("Soumise à la PDP")
    QUEUED = "QUEUED", _("En file d'attente PDP")
    SENT = "SENT", _("Transmise au destinataire")
    DELIVERED = "DELIVERED", _("Réceptionnée par destinataire")
    APPROVED = "APPROVED", _("Approuvée par destinataire")
    REJECTED = "REJECTED", _("Refusée par destinataire")
    DISPUTED = "DISPUTED", _("Litige")
    PAID = "PAID", _("Encaissée (déclaration paiement)")
    CANCELLED = "CANCELLED", _("Annulée (avant transmission)")
    ARCHIVED = "ARCHIVED", _("Archivée")


# ---------------------------------------------------------------------------
# Forme juridique (subset INSEE) — pour ClientProfile et émetteur
# ---------------------------------------------------------------------------
class LegalForm(models.TextChoices):
    AUTO_ENTREPRENEUR = "AE", _("Auto-entrepreneur / micro-entreprise")
    EI = "EI", _("Entreprise individuelle")
    EURL = "EURL", _("EURL (SARL unipersonnelle)")
    SARL = "SARL", _("SARL")
    SAS = "SAS", _("SAS")
    SASU = "SASU", _("SASU")
    SA = "SA", _("SA")
    SNC = "SNC", _("SNC")
    SCI = "SCI", _("SCI")
    SCOP = "SCOP", _("SCOP")
    ASSOCIATION = "ASSO", _("Association")
    PUBLIC = "PUB", _("Personne publique / collectivité")
    OTHER_FR = "OTH_FR", _("Autre (France)")
    OTHER_EU = "OTH_EU", _("Autre (Union européenne)")
    OTHER_INTL = "OTH_INTL", _("Autre (hors UE)")


# ---------------------------------------------------------------------------
# Helpers exportés (utilisés par builders XML)
# ---------------------------------------------------------------------------
__all__ = [
    "VATCategory",
    "VATEX_REASON_CODES",
    "vatex_choices",
    "UN_UNIT_CODES",
    "unit_code_choices",
    "TransactionType",
    "VATPaymentBasis",
    "InvoiceTypeCode",
    "LifecycleState",
    "LegalForm",
]
