"""Tests du module `legal` — régime fiscal et mentions obligatoires."""

from __future__ import annotations

import pytest
from django.test import override_settings

from apps.einvoicing.legal import (
    get_active_regime,
    get_default_vat_category,
    get_default_vatex_code,
    get_legal_tva_mention,
    is_vat_applicable,
)


class TestRegimeGuyaneArt294:
    """Cas TUS — Guyane, art. 294 CGI : TVA non applicable territorialement."""

    @override_settings(INVOICING={"VAT_REGIME": "DOM_GUYANE_MAYOTTE"})
    def test_mention_is_art_294(self) -> None:
        assert get_legal_tva_mention() == "TVA non applicable, art. 294 du CGI"

    @override_settings(INVOICING={"VAT_REGIME": "DOM_GUYANE_MAYOTTE"})
    def test_default_vat_category_is_o(self) -> None:
        # Outside scope of VAT (territoire hors champ TVA)
        assert get_default_vat_category() == "O"

    @override_settings(INVOICING={"VAT_REGIME": "DOM_GUYANE_MAYOTTE"})
    def test_default_vatex_is_outside_scope(self) -> None:
        assert get_default_vatex_code() == "VATEX-EU-O"

    @override_settings(INVOICING={"VAT_REGIME": "DOM_GUYANE_MAYOTTE"})
    def test_vat_not_applicable(self) -> None:
        assert is_vat_applicable() is False


class TestRegimeFranchiseArt293B:
    """Cas franchise en base — métropole, micro-entreprise sous seuils."""

    @override_settings(INVOICING={"VAT_REGIME": "FRANCHISE"})
    def test_mention_is_art_293_b(self) -> None:
        assert get_legal_tva_mention() == "TVA non applicable, art. 293 B du CGI"

    @override_settings(INVOICING={"VAT_REGIME": "FRANCHISE"})
    def test_default_vat_category_is_e(self) -> None:
        # Exempt — vraie exonération (différent de "Outside scope")
        assert get_default_vat_category() == "E"

    @override_settings(INVOICING={"VAT_REGIME": "FRANCHISE"})
    def test_default_vatex_is_franchise(self) -> None:
        assert get_default_vatex_code() == "VATEX-EU-79-C"


class TestRegimeStandard:
    """Régime normal — TVA effectivement collectée."""

    @override_settings(INVOICING={"VAT_REGIME": "STANDARD"})
    def test_no_legal_mention(self) -> None:
        assert get_legal_tva_mention() == ""

    @override_settings(INVOICING={"VAT_REGIME": "STANDARD"})
    def test_default_vat_category_is_standard(self) -> None:
        assert get_default_vat_category() == "S"

    @override_settings(INVOICING={"VAT_REGIME": "STANDARD"})
    def test_no_default_vatex(self) -> None:
        assert get_default_vatex_code() == ""

    @override_settings(INVOICING={"VAT_REGIME": "STANDARD"})
    def test_vat_is_applicable(self) -> None:
        assert is_vat_applicable() is True


class TestRegimeOverride:
    """Le paramètre override prime sur les settings."""

    @override_settings(INVOICING={"VAT_REGIME": "STANDARD"})
    def test_override_wins_over_settings(self) -> None:
        assert get_active_regime("DOM_GUYANE_MAYOTTE") == "DOM_GUYANE_MAYOTTE"
        assert get_legal_tva_mention("DOM_GUYANE_MAYOTTE") == "TVA non applicable, art. 294 du CGI"


class TestUnknownRegimeFallsBackToStandard:
    @override_settings(INVOICING={"VAT_REGIME": "INEXISTANT"})
    def test_unknown_regime_returns_standard(self) -> None:
        assert get_legal_tva_mention() == ""
        assert get_default_vat_category() == "S"
