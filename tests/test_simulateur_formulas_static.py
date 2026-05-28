"""Static regression checks for high-risk client-side simulator formulas."""
from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SIMULATEUR_DIR = ROOT / 'templates' / 'simulateur'


def template_text(filename: str) -> str:
    return (SIMULATEUR_DIR / filename).read_text(encoding='utf-8')


def test_roi_marketing_uses_margin_break_even() -> None:
    text = template_text('roi_marketing.html')
    assert 'marketingRentable()' in text
    assert 'roasSeuil()' in text
    assert 'roas() >= 1' not in text


def test_retention_gain_uses_margin_not_raw_revenue() -> None:
    text = template_text('retention.html')
    assert 'margeAdditionnelle' in text
    assert 'ecartMarge5Ans()' in text
    assert 'return this.ecartMarge5Ans() - this.coutProgramme5Ans();' in text
    assert '+5% de rétention = +25 à +95% de profit' not in text
    assert 'ROI net à 5 ans' not in text


def test_non_quality_roi_keeps_negative_recurring_economics() -> None:
    text = template_text('cout_non_qualite.html')
    assert 'economieNette() { return this.economieMensuelle() - this.coutRecurrent; }' in text
    assert 'Math.max(0, this.economieMensuelle() - this.coutRecurrent)' not in text


def test_inaction_ratio_and_default_are_conservative() -> None:
    text = template_text('cout_inaction.html')
    assert 'aggravation: 0' in text
    assert 'ratioSolution24()' in text
    assert 'coutSolution || 1' not in text


def test_plafond_uses_entered_current_project_baseline() -> None:
    text = template_text('plafond.html')
    assert 'capaciteActuelle() { return this.projetsActuels; }' in text
    assert "['projetsActuels'" in text


def test_capacite_exposes_billable_weeks() -> None:
    text = template_text('capacite.html')
    assert 'semainesFacturables' in text
    assert '* 47' not in text


def test_concentration_tools_warn_on_incomplete_shares() -> None:
    dependance = template_text('dependance.html')
    fournisseurs = template_text('vulnerabilite_fournisseur.html')
    assert 'repartitionWarning()' in dependance
    assert 'totalPct() !== 100' in dependance
    assert 'partWarning()' in fournisseurs
    assert 'totalPart() !== 100' in fournisseurs


def test_pricing_psychologique_remains_indicative() -> None:
    text = template_text('prix_psychologique.html')
    hub = template_text('hub.html')
    assert 'Prix psychologique indicatif' in text
    assert 'Dans ces hypothèses' in text
    assert 'Prix psychologique recommandé' not in text
    assert 'Prix recommandé' not in text
    assert 'Sous-tarification structurelle' not in text
    assert 'vous coulez' not in template_text('dependance.html')
    assert 'sous-tarification structurelle' not in hub
