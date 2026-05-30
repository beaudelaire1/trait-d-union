"""Tests unitaires des validators réglementaires.

Toute la conformité Phase 1 repose sur ces contrôles : Luhn, formats UE,
mod 97 IBAN, formats Peppol/APE. On teste cas nominaux + edge cases.
"""

from __future__ import annotations

import pytest
from django.core.exceptions import ValidationError

from apps.einvoicing.validators import (
    validate_ape_code,
    validate_iban,
    validate_peppol_id,
    validate_siren,
    validate_siret,
    validate_vat_intracom,
)


# ---------------------------------------------------------------------------
# Sample SIREN / SIRET réels avec clés Luhn correctes (sources publiques)
# ---------------------------------------------------------------------------
# Trait d'Union Studio (TUS) : 908 264 112 — SIRET 908 264 112 00016
TUS_SIREN = "908264112"
TUS_SIRET = "90826411200016"
LA_POSTE_SIREN = "356000000"
LA_POSTE_SIRET = "35600000000006"  # somme des 14 chiffres = 20 → multiple de 5


# ---------------------------------------------------------------------------
# SIREN
# ---------------------------------------------------------------------------
class TestSirenValidator:
    def test_valid_siren_passes(self) -> None:
        validate_siren(TUS_SIREN)
        validate_siren("908 264 112")  # avec espaces

    def test_la_poste_siren_passes(self) -> None:
        validate_siren(LA_POSTE_SIREN)

    def test_empty_value_silent(self) -> None:
        validate_siren(None)
        validate_siren("")
        validate_siren(b"")

    def test_wrong_length(self) -> None:
        with pytest.raises(ValidationError) as exc:
            validate_siren("12345")
        assert exc.value.code == "siren_length"

    def test_wrong_checksum(self) -> None:
        with pytest.raises(ValidationError) as exc:
            validate_siren("908264113")  # dernier chiffre cassé
        assert exc.value.code == "siren_checksum"


# ---------------------------------------------------------------------------
# SIRET
# ---------------------------------------------------------------------------
class TestSiretValidator:
    def test_valid_siret_passes(self) -> None:
        validate_siret(TUS_SIRET)

    def test_la_poste_siret_passes(self) -> None:
        validate_siret(LA_POSTE_SIRET)

    def test_wrong_length(self) -> None:
        with pytest.raises(ValidationError) as exc:
            validate_siret("908264112")  # SIREN, pas SIRET
        assert exc.value.code == "siret_length"

    def test_wrong_checksum(self) -> None:
        with pytest.raises(ValidationError) as exc:
            validate_siret("90826411200017")
        assert exc.value.code == "siret_checksum"


# ---------------------------------------------------------------------------
# TVA intracommunautaire
# ---------------------------------------------------------------------------
class TestVATIntracomValidator:
    def test_valid_french_vat(self) -> None:
        # FR + clé 2 chars + SIREN valide
        # Clé FR = 12 + (3 * SIREN) % 97 — pour 908264112, clé = (12 + 3*908264112) % 97 = 91
        validate_vat_intracom("FR91908264112")

    def test_valid_german_vat(self) -> None:
        validate_vat_intracom("DE123456789")

    def test_empty_silent(self) -> None:
        validate_vat_intracom(None)

    def test_wrong_length(self) -> None:
        with pytest.raises(ValidationError):
            validate_vat_intracom("FR")

    def test_french_vat_with_invalid_siren_part(self) -> None:
        with pytest.raises(ValidationError) as exc:
            validate_vat_intracom("FR99123456789")
        assert exc.value.code == "vat_fr_siren"


# ---------------------------------------------------------------------------
# IBAN
# ---------------------------------------------------------------------------
class TestIBANValidator:
    def test_valid_french_iban(self) -> None:
        validate_iban("FR1420041010050500013M02606")

    def test_valid_german_iban(self) -> None:
        validate_iban("DE89370400440532013000")

    def test_empty_silent(self) -> None:
        validate_iban("")

    def test_wrong_country_length(self) -> None:
        with pytest.raises(ValidationError) as exc:
            validate_iban("FR142004101005050001")  # trop court
        assert exc.value.code in {"iban_country_length", "iban_length"}

    def test_wrong_checksum(self) -> None:
        with pytest.raises(ValidationError) as exc:
            validate_iban("FR1420041010050500013M02607")  # dernier chiffre cassé
        assert exc.value.code == "iban_checksum"


# ---------------------------------------------------------------------------
# Peppol Participant ID
# ---------------------------------------------------------------------------
class TestPeppolValidator:
    @pytest.mark.parametrize(
        "value",
        [
            "0009:90826411200016",  # SIRET FR
            "0002:908264112",       # SIREN FR
            "0088:7300010000001",   # GLN
        ],
    )
    def test_valid_peppol(self, value: str) -> None:
        validate_peppol_id(value)

    @pytest.mark.parametrize(
        "value",
        ["", "abc:123", "12:0001", "0009-90826411200016", "00091:90826411200016"],
    )
    def test_invalid_peppol(self, value: str) -> None:
        if value == "":
            validate_peppol_id(value)  # silent
        else:
            with pytest.raises(ValidationError):
                validate_peppol_id(value)


# ---------------------------------------------------------------------------
# Code APE / NAF
# ---------------------------------------------------------------------------
class TestAPECodeValidator:
    def test_valid_codes(self) -> None:
        validate_ape_code("6201Z")
        validate_ape_code("8559A")

    def test_with_dot(self) -> None:
        # On accepte "62.01Z" (les caractères non alphanum sont normalisés)
        validate_ape_code("62.01Z")

    def test_invalid(self) -> None:
        with pytest.raises(ValidationError):
            validate_ape_code("ABC123")
