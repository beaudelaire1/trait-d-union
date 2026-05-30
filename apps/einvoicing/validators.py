"""
Validators réglementaires pour la facturation électronique française.

Tous les validators :
- ne lèvent que des `ValidationError` Django (pour usage `clean()` / forms)
- acceptent `None` ou chaîne vide → silencieux (champ optionnel : utilisez `blank=False`)
- normalisent l'entrée (espaces, casse) avant contrôle

Couvre :
- SIREN (9 chiffres + clé Luhn)
- SIRET (14 chiffres + clé Luhn — règle spéciale pour La Poste)
- TVA intracommunautaire (FR + UE basique)
- IBAN (mod 97)
- Peppol Participant ID (`<scheme>:<value>`)
- Code APE/NAF (4 chiffres + 1 lettre)

Références :
- INSEE — règle SIREN/SIRET (Luhn)
- Wikipedia — IBAN check digits ISO 13616
- OpenPeppol — Participant Identifier scheme
"""

from __future__ import annotations

import re
import string
from typing import Optional

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _normalize_digits(value: Optional[str]) -> str:
    """Retire tous les caractères non numériques."""
    if not value:
        return ""
    return re.sub(r"\D", "", str(value))


def _normalize_alphanum(value: Optional[str]) -> str:
    """Uppercase + retire tout sauf [A-Z0-9]."""
    if not value:
        return ""
    return re.sub(r"[^A-Z0-9]", "", str(value).upper())


def _luhn_checksum_ok(digits: str) -> bool:
    """Validation par algorithme de Luhn (MOD 10).

    Implémentation auditable. Les chiffres en position paire (depuis la droite,
    indexée à partir de 1) sont doublés ; si le double dépasse 9, on soustrait 9.
    La somme totale doit être divisible par 10.
    """
    if not digits.isdigit() or len(digits) < 2:
        return False
    total = 0
    # Itération de droite à gauche
    for i, ch in enumerate(reversed(digits)):
        n = ord(ch) - 48  # int(ch) plus rapide
        if i % 2 == 1:
            n *= 2
            if n > 9:
                n -= 9
        total += n
    return total % 10 == 0


# ---------------------------------------------------------------------------
# SIREN / SIRET
# ---------------------------------------------------------------------------
SIREN_LA_POSTE = "356000000"  # exception INSEE : la somme des chiffres doit être ≡ 0 mod 5


def validate_siren(value: Optional[str]) -> None:
    """Valide un SIREN (9 chiffres + Luhn).

    - Champ vide → silencieux (utiliser `blank=False` pour rendre obligatoire).
    """
    if value in (None, "", b""):
        return
    digits = _normalize_digits(value)
    if len(digits) != 9:
        raise ValidationError(
            _("Le SIREN doit contenir exactement 9 chiffres (reçu : %(n)d)."),
            params={"n": len(digits)},
            code="siren_length",
        )
    # Cas spécial La Poste
    if digits == SIREN_LA_POSTE:
        return
    if not _luhn_checksum_ok(digits):
        raise ValidationError(
            _("SIREN invalide : la clé de contrôle Luhn n'est pas correcte."),
            code="siren_checksum",
        )


def validate_siret(value: Optional[str]) -> None:
    """Valide un SIRET (14 chiffres + Luhn).

    - Le SIRET = SIREN (9) + NIC (5).
    - Cas particulier des établissements de La Poste : la somme des 14 chiffres
      doit être un multiple de 5 (et non Luhn standard).
    """
    if value in (None, "", b""):
        return
    digits = _normalize_digits(value)
    if len(digits) != 14:
        raise ValidationError(
            _("Le SIRET doit contenir exactement 14 chiffres (reçu : %(n)d)."),
            params={"n": len(digits)},
            code="siret_length",
        )
    siren = digits[:9]
    if siren == SIREN_LA_POSTE:
        if sum(int(c) for c in digits) % 5 != 0:
            raise ValidationError(
                _("SIRET La Poste invalide : somme des chiffres non multiple de 5."),
                code="siret_la_poste_checksum",
            )
        return
    if not _luhn_checksum_ok(digits):
        raise ValidationError(
            _("SIRET invalide : la clé de contrôle Luhn n'est pas correcte."),
            code="siret_checksum",
        )


# ---------------------------------------------------------------------------
# TVA intracommunautaire
# ---------------------------------------------------------------------------
# Format simplifié — la validation forte se fait via VIES (hors scope validator local).
# Couvre les 27 préfixes UE + les 8 plus stricts (longueur exacte).
_VAT_PATTERNS = {
    "FR": re.compile(r"^FR[A-HJ-NP-Z0-9]{2}\d{9}$"),  # 2 chars + 9 digits SIREN
    "DE": re.compile(r"^DE\d{9}$"),
    "IT": re.compile(r"^IT\d{11}$"),
    "ES": re.compile(r"^ES[A-Z0-9]\d{7}[A-Z0-9]$"),
    "BE": re.compile(r"^BE0\d{9}$"),
    "NL": re.compile(r"^NL\d{9}B\d{2}$"),
    "LU": re.compile(r"^LU\d{8}$"),
    "PT": re.compile(r"^PT\d{9}$"),
}
_VAT_GENERIC = re.compile(r"^[A-Z]{2}[A-Z0-9]{2,12}$")


def validate_vat_intracom(value: Optional[str]) -> None:
    """Valide un numéro de TVA intracommunautaire.

    La validation est syntaxique (pattern par pays + fallback générique UE).
    Pour une validation sémantique (entreprise existante), utiliser VIES.
    """
    if value in (None, "", b""):
        return
    v = _normalize_alphanum(value)
    if len(v) < 4 or len(v) > 14:
        raise ValidationError(
            _("Numéro de TVA intracommunautaire invalide (longueur : %(n)d)."),
            params={"n": len(v)},
            code="vat_length",
        )
    country = v[:2]
    pattern = _VAT_PATTERNS.get(country, _VAT_GENERIC)
    if not pattern.match(v):
        raise ValidationError(
            _("Numéro de TVA intracommunautaire %(country)s invalide."),
            params={"country": country},
            code="vat_format",
        )
    # FR : la partie SIREN doit être valide
    if country == "FR":
        siren = v[4:]
        try:
            validate_siren(siren)
        except ValidationError:
            raise ValidationError(
                _("Numéro de TVA FR : la partie SIREN n'est pas valide."),
                code="vat_fr_siren",
            )


# ---------------------------------------------------------------------------
# IBAN — ISO 13616 mod 97
# ---------------------------------------------------------------------------
_IBAN_LENGTHS = {
    "AD": 24, "AE": 23, "AL": 28, "AT": 20, "AZ": 28, "BA": 20, "BE": 16,
    "BG": 22, "BH": 22, "BR": 29, "CH": 21, "CR": 22, "CY": 28, "CZ": 24,
    "DE": 22, "DK": 18, "DO": 28, "EE": 20, "ES": 24, "FI": 18, "FO": 18,
    "FR": 27, "GB": 22, "GE": 22, "GI": 23, "GL": 18, "GR": 27, "GT": 28,
    "HR": 21, "HU": 28, "IE": 22, "IL": 23, "IS": 26, "IT": 27, "JO": 30,
    "KW": 30, "KZ": 20, "LB": 28, "LI": 21, "LT": 20, "LU": 20, "LV": 21,
    "MC": 27, "MD": 24, "ME": 22, "MK": 19, "MR": 27, "MT": 31, "MU": 30,
    "NL": 18, "NO": 15, "PK": 24, "PL": 28, "PS": 29, "PT": 25, "QA": 29,
    "RO": 24, "RS": 22, "SA": 24, "SE": 24, "SI": 19, "SK": 24, "SM": 27,
    "TN": 24, "TR": 26, "VG": 24, "XK": 20,
}


def validate_iban(value: Optional[str]) -> None:
    """Valide un IBAN (longueur par pays + check digits ISO 13616 mod 97)."""
    if value in (None, "", b""):
        return
    iban = _normalize_alphanum(value)
    if len(iban) < 15 or len(iban) > 34:
        raise ValidationError(_("IBAN : longueur hors limites."), code="iban_length")
    country = iban[:2]
    expected = _IBAN_LENGTHS.get(country)
    if expected is not None and len(iban) != expected:
        raise ValidationError(
            _("IBAN %(country)s : %(expected)d caractères attendus, %(got)d reçus."),
            params={"country": country, "expected": expected, "got": len(iban)},
            code="iban_country_length",
        )
    # Réarrangement : déplacer les 4 premiers caractères à la fin
    rearranged = iban[4:] + iban[:4]
    # Convertir lettres → chiffres : A=10, B=11, ..., Z=35
    converted = []
    for ch in rearranged:
        if ch.isdigit():
            converted.append(ch)
        elif ch in string.ascii_uppercase:
            converted.append(str(ord(ch) - 55))
        else:
            raise ValidationError(_("IBAN : caractère invalide."), code="iban_charset")
    number = int("".join(converted))
    if number % 97 != 1:
        raise ValidationError(
            _("IBAN invalide : la clé de contrôle (mod 97) n'est pas correcte."),
            code="iban_checksum",
        )


# ---------------------------------------------------------------------------
# Peppol Participant Identifier — `scheme:value`
# Le schéma le plus courant en FR est `0009` (SIRET) et `0002` (SIREN).
# ---------------------------------------------------------------------------
_PEPPOL_PATTERN = re.compile(r"^[0-9]{4}:[A-Za-z0-9._\-]{1,50}$")


def validate_peppol_id(value: Optional[str]) -> None:
    """Valide un identifiant Peppol au format `scheme:value`."""
    if value in (None, "", b""):
        return
    if not _PEPPOL_PATTERN.match(str(value).strip()):
        raise ValidationError(
            _("Identifiant Peppol invalide. Format attendu : `<scheme>:<value>` (ex. 0009:90826411200016)."),
            code="peppol_format",
        )


# ---------------------------------------------------------------------------
# Code APE / NAF — 4 chiffres + 1 lettre (ex. 6201Z)
# ---------------------------------------------------------------------------
_APE_PATTERN = re.compile(r"^\d{4}[A-Z]$")


def validate_ape_code(value: Optional[str]) -> None:
    """Valide un code APE / NAF (ex. 6201Z)."""
    if value in (None, "", b""):
        return
    v = _normalize_alphanum(value)
    if not _APE_PATTERN.match(v):
        raise ValidationError(
            _("Code APE/NAF invalide. Format attendu : 4 chiffres + 1 lettre (ex. 6201Z)."),
            code="ape_format",
        )


__all__ = [
    "validate_siren",
    "validate_siret",
    "validate_vat_intracom",
    "validate_iban",
    "validate_peppol_id",
    "validate_ape_code",
]
