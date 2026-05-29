"""Tests du moteur de scoring du diagnostic terrain.

Vérifient l'objectivité et le déterminisme du scoring :
  • cohérence des KPIs dérivés ;
  • zones de danger alignées sur le guide TUS ;
  • bornage strict des scores (0..10 par domaine, 0..100 global) ;
  • niveau d'urgence selon la règle des signaux simultanés ;
  • robustesse aux réponses manquantes.
"""
import pytest

from apps.diagnostic.field_scoring import (
    analyze, compute_kpis, compute_domain_scores, compute_global_score,
    detect_signals, urgency_level,
)
from apps.diagnostic.field_questions import (
    questions_for_profile, PROFILES, SECTORS, QUESTIONS,
)


# ── Jeux de réponses ─────────────────────────────────────────────────
HEALTHY = {
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

DISTRESSED = {
    "ca_mensuel": "10000", "charges_fixes": "8500",
    "charges_variables_pct": "75", "tresorerie_actuelle": "1000",
    "encaissements_30j": "3000", "decaissements_30j": "9000",
    "delai_paiement": "75", "devis_envoyes": "10", "devis_signes": "1",
    "nb_clients_actifs": "5", "part_plus_gros_client": "60",
    "budget_marketing": "800", "nouveaux_clients": "1",
    "ca_recurrent_pct": "5", "heures_travaillees": "60",
    "heures_facturees": "15", "taux_horaire": "40", "nb_outils_saas": "22",
    "friction_niveau": "5", "effectif": "3", "delegation_niveau": "1",
    "nb_offres": "14", "saisonnalite": "5", "pricing_maitrise": "1",
    "derniere_hausse_prix": "jamais", "part_plus_gros_fournisseur": "70",
    "exposition_import": "5", "homme_cle": "5", "part_ca_public": "60",
    "tresorerie_secours": "0",
}


# ── KPIs ─────────────────────────────────────────────────────────────
def test_kpi_tresorerie_30j_formula():
    kpis = compute_kpis(HEALTHY)
    # 15000 + 18000 - 9000 = 24000
    assert kpis["treso_30j"].value == 24000
    assert kpis["treso_30j"].status == "good"


def test_kpi_tresorerie_negative_is_danger():
    kpis = compute_kpis(DISTRESSED)
    # 1000 + 3000 - 9000 = -5000
    assert kpis["treso_30j"].value == -5000
    assert kpis["treso_30j"].status == "danger"


def test_kpi_marge_brute_complement_of_variable_costs():
    kpis = compute_kpis(HEALTHY)
    assert kpis["marge_brute"].value == 75  # 100 - 25


def test_kpi_conversion_ratio():
    kpis = compute_kpis(HEALTHY)
    assert kpis["conversion"].value == 50.0  # 5/10
    assert kpis["conversion"].status == "good"


def test_kpi_dso_danger_above_45():
    kpis = compute_kpis(DISTRESSED)
    assert kpis["dso"].value == 75
    assert kpis["dso"].status == "danger"


def test_kpi_couverture_charges_danger():
    kpis = compute_kpis(DISTRESSED)
    # marge brute = 25% de 10000 = 2500 ; couverture = 8500/2500 = 340%
    assert kpis["couverture"].value == 340.0
    assert kpis["couverture"].status == "danger"


# ── Scores bornés ────────────────────────────────────────────────────
def test_domain_scores_bounded():
    for answers in (HEALTHY, DISTRESSED):
        kpis = compute_kpis(answers)
        domains = compute_domain_scores(answers, kpis)
        for score in domains.values():
            assert score is None or 0 <= score <= 10


def test_global_score_bounded_and_ordered():
    healthy_kpis = compute_kpis(HEALTHY)
    distressed_kpis = compute_kpis(DISTRESSED)
    healthy = compute_global_score(
        compute_domain_scores(HEALTHY, healthy_kpis), "pme")
    distressed = compute_global_score(
        compute_domain_scores(DISTRESSED, distressed_kpis), "pme")
    assert 0 <= distressed <= 100
    assert 0 <= healthy <= 100
    # Une entreprise saine doit scorer nettement mieux qu'une en détresse
    assert healthy > distressed
    assert healthy >= 70
    assert distressed <= 35


# ── Signaux & urgence ────────────────────────────────────────────────
def test_healthy_has_no_critical_signals():
    kpis = compute_kpis(HEALTHY)
    signals = detect_signals(kpis)
    assert all(s.severity != "critical" for s in signals)
    assert urgency_level(signals)["level"] == "sain"


def test_distressed_triggers_urgency():
    kpis = compute_kpis(DISTRESSED)
    signals = detect_signals(kpis)
    assert any(s.severity == "critical" for s in signals)
    assert urgency_level(signals)["level"] == "urgence"


# ── Robustesse ───────────────────────────────────────────────────────
def test_empty_answers_do_not_crash():
    report = analyze({}, "pme")
    assert report["global_score"] == 0
    assert isinstance(report["kpis"], list)
    assert isinstance(report["recommendations"], list)


def test_partial_answers_skip_missing_kpis():
    kpis = compute_kpis({"ca_mensuel": "10000"})
    assert kpis["dso"].status == "na"
    assert kpis["conversion"].status == "na"


@pytest.mark.parametrize("profile", list(PROFILES.keys()))
def test_analyze_full_report_structure(profile):
    report = analyze(HEALTHY, profile)
    assert report["profile"] == profile
    assert "verdict" in report and "label" in report["verdict"]
    assert "urgency" in report
    assert len(report["domain_scores"]) == 5
    assert report["recommendations"]  # toujours au moins une reco


@pytest.mark.parametrize("profile", list(PROFILES.keys()))
def test_questions_filtered_by_profile(profile):
    qs = questions_for_profile(profile)
    assert qs  # non vide
    assert all(profile in q.profiles for q in qs)


def test_invalid_profile_falls_back_to_pme():
    report = analyze(HEALTHY, "inexistant")
    assert report["profile"] == "pme"


# ── Filtrage par secteur ─────────────────────────────────────────────
def test_sector_specific_questions_hidden_without_sector():
    """Sans secteur, seules les questions universelles apparaissent."""
    qs = questions_for_profile("pme")
    assert all(not q.sectors for q in qs)


def test_sector_adds_targeted_questions():
    """Choisir un secteur fait apparaître les questions ciblées."""
    base = questions_for_profile("pme")
    restau = questions_for_profile("pme", "restauration")
    assert len(restau) > len(base)
    ids = {q.id for q in restau}
    assert "panier_moyen" in ids  # ciblée restauration


def test_sector_question_not_leaking_to_other_sector():
    btp = {q.id for q in questions_for_profile("pme", "btp")}
    assert "panier_moyen" not in btp  # panier_moyen ne cible pas le BTP
    assert "carnet_commandes" in btp  # mais le carnet de commandes oui


def test_all_questions_have_short_label():
    """Chaque question porte un libellé court pour les rapports."""
    assert all(q.short for q in QUESTIONS)


def test_questions_are_phrased_as_questions():
    """Les intitulés sont de vraies questions (terminées par ?)."""
    interrogatives = [q for q in QUESTIONS if q.label.strip().endswith("?")]
    # La grande majorité doit être formulée en question.
    assert len(interrogatives) >= len(QUESTIONS) * 0.8


@pytest.mark.parametrize("profile", list(PROFILES.keys()))
def test_every_profile_scores(profile):
    """Les 6 profils produisent un score borné et un verdict."""
    report = analyze(HEALTHY, profile)
    assert 0 <= report["global_score"] <= 100
    assert report["verdict"]["label"]


# ── Intégration des vues (flux complet) ──────────────────────────────
@pytest.fixture
def staff_client(db, client, django_user_model):
    user = django_user_model.objects.create_user(
        username="diagstaff", password="x", email="d@test.com", is_staff=True,
    )
    client.force_login(user)
    return client


@pytest.mark.django_db
def test_diagnostic_home_renders(staff_client):
    resp = staff_client.get("/tus-gestion-secure/diagnostic/")
    assert resp.status_code == 200
    assert b"Centre de diagnostic" in resp.content


@pytest.mark.django_db
def test_field_new_creates_and_redirects(staff_client):
    resp = staff_client.post("/tus-gestion-secure/diagnostic/terrain/nouveau/", {
        "company_name": "Test SARL", "profile": "pme", "sector": "services",
    })
    assert resp.status_code == 302
    from apps.diagnostic.models import FieldDiagnostic
    diag = FieldDiagnostic.objects.get(company_name="Test SARL")
    assert diag.profile == "pme"
    assert f"/terrain/{diag.pk}/questionnaire/" in resp["Location"]


@pytest.mark.django_db
def test_field_form_scores_on_submit(staff_client):
    from apps.diagnostic.models import FieldDiagnostic
    diag = FieldDiagnostic.objects.create(company_name="Scored", profile="pme")
    resp = staff_client.post(
        f"/tus-gestion-secure/diagnostic/terrain/{diag.pk}/questionnaire/",
        HEALTHY,
    )
    assert resp.status_code == 302
    diag.refresh_from_db()
    assert diag.overall_score >= 70
    assert diag.results["verdict"]["label"]


@pytest.mark.django_db
def test_field_detail_renders(staff_client):
    from apps.diagnostic.models import FieldDiagnostic
    diag = FieldDiagnostic.objects.create(company_name="Detail Co", profile="solo")
    diag.results = analyze(HEALTHY, "solo")
    diag.overall_score = diag.results["global_score"]
    diag.save()
    resp = staff_client.get(f"/tus-gestion-secure/diagnostic/terrain/{diag.pk}/")
    assert resp.status_code == 200
    assert b"Detail Co" in resp.content


@pytest.mark.django_db
def test_field_pdf_generates(staff_client):
    pytest.importorskip("weasyprint")
    from apps.diagnostic.models import FieldDiagnostic
    diag = FieldDiagnostic.objects.create(company_name="PDF Co", profile="pme")
    diag.results = analyze(HEALTHY, "pme")
    diag.overall_score = diag.results["global_score"]
    diag.save()
    resp = staff_client.get(f"/tus-gestion-secure/diagnostic/terrain/{diag.pk}/pdf/")
    assert resp.status_code == 200
    assert resp["Content-Type"] == "application/pdf"
    assert resp.content[:4] == b"%PDF"
