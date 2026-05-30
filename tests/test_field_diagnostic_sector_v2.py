"""Tests Diagnostic v2 — calibration sectorielle (Paliers 1 + 2).

Couvre :
- AC-D1 : pondérations surchargées par secteur appliquées
- AC-D2 : fallback systématique sur la matrice universelle
- AC-D3 : seuils sectoriels appliqués sur DSO / marge / couverture / dépendance
- AC-D4 : `scoring_version: 2` présent dans les résultats
- AC-D5 : le détail KPI mentionne le contexte sectoriel
- AC-D7 : impact mesurable sur le score global d'une PME BTP à risques
"""
from __future__ import annotations

import pytest

from apps.diagnostic.field_scoring import (
    analyze,
    compute_kpis,
    compute_global_score,
    compute_domain_scores,
)
from apps.diagnostic.sector_calibration import (
    SCORING_VERSION,
    DOMAIN_WEIGHTS_BY_SECTOR,
    KPI_THRESHOLDS_BY_SECTOR,
    SectorContext,
    get_domain_weights,
    get_kpi_thresholds,
    is_kpi_hidden,
)


# ── Données réutilisables ──────────────────────────────────────────────
HEALTHY_PME = {
    "ca_mensuel": "20000", "charges_fixes": "6000",
    "charges_variables_pct": "25", "tresorerie_actuelle": "15000",
    "encaissements_30j": "18000", "decaissements_30j": "9000",
    "delai_paiement": "25", "devis_envoyes": "10", "devis_signes": "5",
    "nb_clients_actifs": "30", "part_plus_gros_client": "12",
    "budget_marketing": "500", "nouveaux_clients": "4",
    "ca_recurrent_pct": "55", "heures_travaillees": "40",
    "heures_facturees": "30", "taux_horaire": "80", "nb_outils_saas": "5",
    "friction_niveau": "1", "effectif": "5", "delegation_niveau": "5",
    "nb_offres": "4", "saisonnalite": "1", "pricing_maitrise": "5",
    "derniere_hausse_prix": "recent", "part_plus_gros_fournisseur": "12",
    "exposition_import": "1", "homme_cle": "1", "part_ca_public": "5",
    "tresorerie_secours": "8",
}

# PME BTP "réaliste" : risques structurellement élevés (DOM)
BTP_REALISTE = {
    "ca_mensuel": "60000", "charges_fixes": "20000",
    "charges_variables_pct": "65", "tresorerie_actuelle": "25000",
    "encaissements_30j": "55000", "decaissements_30j": "45000",
    "delai_paiement": "60",  # Norme BTP / commande publique
    "devis_envoyes": "8", "devis_signes": "3",
    "nb_clients_actifs": "12", "part_plus_gros_client": "32",
    "budget_marketing": "300", "nouveaux_clients": "1",
    "ca_recurrent_pct": "10",
    "nb_outils_saas": "10", "friction_niveau": "3",
    "effectif": "10", "delegation_niveau": "3",
    "nb_offres": "3", "saisonnalite": "3", "pricing_maitrise": "3",
    "derniere_hausse_prix": "moyen",
    "part_plus_gros_fournisseur": "55",  # appro DOM concentré
    "exposition_import": "5",            # tout importé
    "homme_cle": "4", "part_ca_public": "60",
    "tresorerie_secours": "1",
}

# E-commerce "réaliste" : DSO doit rester court, charges fixes faibles
ECOMMERCE_REALISTE = {
    "ca_mensuel": "50000", "charges_fixes": "8000",
    "charges_variables_pct": "55",
    "tresorerie_actuelle": "30000",
    "encaissements_30j": "50000", "decaissements_30j": "30000",
    "delai_paiement": "5",  # paiement immédiat
    "devis_envoyes": "0", "devis_signes": "0",
    "nb_clients_actifs": "1500", "part_plus_gros_client": "2",
    "budget_marketing": "5000", "nouveaux_clients": "150",
    "ca_recurrent_pct": "15",
    "nb_outils_saas": "12", "friction_niveau": "2",
    "effectif": "4", "delegation_niveau": "4",
    "nb_offres": "5", "saisonnalite": "3", "pricing_maitrise": "4",
    "derniere_hausse_prix": "recent",
    "part_plus_gros_fournisseur": "30",
    "exposition_import": "3", "homme_cle": "2",
    "part_ca_public": "0", "tresorerie_secours": "3",
}


# ════════════════════════════════════════════════════════════════════
# AC-D1 / AC-D2 — Pondérations sectorielles
# ════════════════════════════════════════════════════════════════════

class TestSectorWeights:
    def test_weights_match_calibration_table(self) -> None:
        """Les pondérations renvoyées correspondent bien à la table."""
        weights = get_domain_weights("pme", "btp")
        expected = DOMAIN_WEIGHTS_BY_SECTOR["btp"]["pme"]
        assert weights == expected
        # Vérifie que les risques pèsent plus en BTP qu'en PME générique
        assert weights["risques"] >= 0.20

    def test_weights_fallback_when_sector_missing(self) -> None:
        """Si le secteur n'est pas dans la table, fallback (None retourné)."""
        assert get_domain_weights("pme", "secteur_inconnu") is None

    def test_weights_fallback_when_no_sector(self) -> None:
        assert get_domain_weights("pme", None) is None
        assert get_domain_weights("pme", "") is None

    def test_weights_fallback_when_profile_missing_for_sector(self) -> None:
        """BTP n'a pas (encore) de surcharge pour 'reprise' → fallback."""
        assert get_domain_weights("reprise", "btp") is None


# ════════════════════════════════════════════════════════════════════
# AC-D3 — Seuils sectoriels des KPIs
# ════════════════════════════════════════════════════════════════════

class TestSectorThresholds:
    def test_dso_btp_more_tolerant(self) -> None:
        """DSO BTP : seuil 'good' > 30 j (norme universelle)."""
        good, danger = get_kpi_thresholds("dso", "btp")
        assert good >= 45 and danger >= 75

    def test_dso_ecommerce_stricter(self) -> None:
        """DSO e-commerce : seuils stricts (paiement immédiat attendu)."""
        good, danger = get_kpi_thresholds("dso", "ecommerce")
        assert good <= 10 and danger <= 30

    def test_dso_restauration_hidden(self) -> None:
        """DSO restauration → KPI non pertinent (encaissement immédiat)."""
        assert is_kpi_hidden("dso", "restauration")
        assert get_kpi_thresholds("dso", "restauration") is None

    def test_marge_brute_conseil_higher(self) -> None:
        """Marge brute attendue plus élevée pour le conseil."""
        good, _ = get_kpi_thresholds("marge_brute", "conseil")
        assert good >= 70

    def test_marge_brute_btp_lower(self) -> None:
        """Marge brute BTP : seuil good plus bas (matériaux + sous-traitance)."""
        good, _ = get_kpi_thresholds("marge_brute", "btp")
        assert good <= 40

    def test_dependance_client_diffuse_hidden(self) -> None:
        """Dépendance client : non pertinente pour B2C diffus."""
        for sector in ("commerce", "ecommerce", "restauration", "beaute"):
            assert is_kpi_hidden("dependance_client", sector), sector


# ════════════════════════════════════════════════════════════════════
# Application réelle dans compute_kpis
# ════════════════════════════════════════════════════════════════════

class TestComputeKpisWithSector:
    def test_dso_btp_60days_is_warn_not_danger(self) -> None:
        """Un DSO de 60 j en BTP doit être 'warn' ou 'good', PAS 'danger'."""
        kpis_universal = compute_kpis(BTP_REALISTE, sector=None)
        kpis_btp = compute_kpis(BTP_REALISTE, sector="btp")
        # Universellement : 60 j = danger
        assert kpis_universal["dso"].status == "danger"
        # En BTP : 60 j est dans la zone d'avertissement (good=45, danger=90)
        assert kpis_btp["dso"].status == "warn"

    def test_dso_ecommerce_30days_is_danger(self) -> None:
        """30 j en e-commerce → danger (alors qu'universellement seulement 'warn')."""
        answers = {**ECOMMERCE_REALISTE, "delai_paiement": "30"}
        kpis_universal = compute_kpis(answers, sector=None)
        kpis_eco = compute_kpis(answers, sector="ecommerce")
        # Universellement : 30 j = good (≤ 30 = good)
        assert kpis_universal["dso"].status == "good"
        # En e-commerce : 30 j = danger (≥ 30 = danger)
        assert kpis_eco["dso"].status == "danger"

    def test_dso_hidden_for_restaurant(self) -> None:
        """En restauration, le KPI DSO doit être 'na' (non pertinent)."""
        answers = {**HEALTHY_PME, "delai_paiement": "60"}
        kpis = compute_kpis(answers, sector="restauration")
        assert kpis["dso"].status == "na"
        assert kpis["dso"].value is None

    def test_marge_btp_25pct_is_acceptable(self) -> None:
        """Une marge brute de 25 % en BTP doit être 'warn' ou 'good', pas danger."""
        answers = {**BTP_REALISTE, "charges_variables_pct": "75"}  # marge 25 %
        kpis_universal = compute_kpis(answers, sector=None)
        kpis_btp = compute_kpis(answers, sector="btp")
        # Universellement : 25 % de marge = danger (good=50, danger=30)
        assert kpis_universal["marge_brute"].status == "danger"
        # En BTP : 25 % entre 15 (danger) et 35 (good) → warn
        assert kpis_btp["marge_brute"].status == "warn"

    def test_dependance_client_hidden_for_b2c(self) -> None:
        """Pour un commerce, le KPI dépendance client doit être masqué."""
        kpis = compute_kpis(BTP_REALISTE, sector="commerce")
        assert kpis["dependance_client"].status == "na"


# ════════════════════════════════════════════════════════════════════
# Application dans compute_global_score
# ════════════════════════════════════════════════════════════════════

class TestComputeGlobalScoreWithSector:
    def test_btp_with_high_risks_scores_lower_with_sector(self) -> None:
        """AC-D7 — Pour une PME BTP avec risques élevés, le score sectoriel
        doit être inférieur ou égal au score universel (les risques sont
        sur-pondérés en BTP)."""
        kpis_btp = compute_kpis(BTP_REALISTE, sector="btp")
        domains = compute_domain_scores(BTP_REALISTE, kpis_btp)
        score_universal = compute_global_score(domains, "pme", sector=None)
        score_btp = compute_global_score(domains, "pme", sector="btp")
        # Le score sectoriel BTP doit être inférieur (risques sur-pondérés
        # → impact négatif si risques bas)
        assert score_btp <= score_universal

    def test_score_unchanged_when_no_sector(self) -> None:
        """compute_global_score sans secteur = comportement v1 (rétro-compat)."""
        kpis = compute_kpis(HEALTHY_PME)
        domains = compute_domain_scores(HEALTHY_PME, kpis)
        s1 = compute_global_score(domains, "pme")
        s2 = compute_global_score(domains, "pme", sector=None)
        s3 = compute_global_score(domains, "pme", sector="")
        assert s1 == s2 == s3


# ════════════════════════════════════════════════════════════════════
# Intégration analyze() — AC-D4 + AC-D5
# ════════════════════════════════════════════════════════════════════

class TestAnalyzeWithSector:
    def test_scoring_version_present(self) -> None:
        report = analyze(HEALTHY_PME, "pme", sector="btp")
        assert report["scoring_version"] == SCORING_VERSION
        assert report["scoring_version"] == 2

    def test_sector_echoed_in_results(self) -> None:
        report = analyze(HEALTHY_PME, "pme", sector="btp")
        assert report["sector"] == "btp"
        assert report["sector_weights_applied"] is True

    def test_no_sector_means_universal_weights(self) -> None:
        report = analyze(HEALTHY_PME, "pme")
        assert report["sector"] == ""
        assert report["sector_weights_applied"] is False

    def test_unknown_sector_falls_back(self) -> None:
        report = analyze(HEALTHY_PME, "pme", sector="unknown_xyz")
        assert report["sector"] == "unknown_xyz"
        assert report["sector_weights_applied"] is False

    def test_kpi_detail_mentions_sector_thresholds(self) -> None:
        """AC-D5 — Le détail KPI doit mentionner les seuils sectoriels quand
        une surcharge existe."""
        report = analyze(BTP_REALISTE, "pme", sector="btp")
        dso_kpi = next(k for k in report["kpis"] if k["key"] == "dso")
        # Le détail mentionne le seuil sectoriel
        assert "secteur" in dso_kpi["detail"].lower() or "ajustés" in dso_kpi["detail"].lower()


# ════════════════════════════════════════════════════════════════════
# Robustesse / non-régression
# ════════════════════════════════════════════════════════════════════

@pytest.mark.parametrize("sector", list(DOMAIN_WEIGHTS_BY_SECTOR.keys()))
def test_every_sector_with_pme_produces_bounded_score(sector: str) -> None:
    """Tous les secteurs déclarés doivent produire un score borné /100."""
    report = analyze(HEALTHY_PME, "pme", sector=sector)
    assert 0 <= report["global_score"] <= 100
    assert report["verdict"]["label"]


def test_empty_answers_with_sector_does_not_crash() -> None:
    report = analyze({}, "pme", sector="btp")
    assert report["global_score"] == 0
    assert isinstance(report["kpis"], list)


def test_sector_context_helper() -> None:
    ctx = SectorContext.for_("pme", "btp")
    assert ctx.sector == "btp"
    assert ctx.weights is not None

    ctx = SectorContext.for_("pme", None)
    assert ctx.sector is None
    assert ctx.weights is None
