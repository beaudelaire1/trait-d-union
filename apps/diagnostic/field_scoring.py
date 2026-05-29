"""Moteur de scoring du diagnostic terrain — Trait d'Union Studio.

Transforme les réponses brutes d'un diagnostic terrain en :

1. **KPIs vitaux dérivés** (trésorerie 30j, DSO, marge brute, couverture des
   charges, taux de conversion, capacité facturable, dépendances…).
2. **Scores par domaine** /10, calculés par seuils objectifs.
3. **Score global** /100, moyenne pondérée des domaines selon le profil.
4. **Signaux d'alerte** classés par sévérité (zones de danger du guide TUS).
5. **Plan d'action priorisé** (🔴 critique → 🟢 bonus).

⚠️ Principe directeur : aucune note subjective. Chaque score découle d'une
formule à seuils documentée, alignée sur les invariants des simulateurs TUS
déjà audités. Le moteur est pur (sans effet de bord) et déterministe.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .field_questions import DOMAINS, PROFILES


# ── Pondération des domaines par profil (somme = 1.0) ────────────────
DOMAIN_WEIGHTS: dict[str, dict[str, float]] = {
    "solo": {
        "finance": 0.30, "commercial": 0.22, "organisation": 0.25,
        "strategie": 0.13, "risques": 0.10,
    },
    "tpe": {
        "finance": 0.30, "commercial": 0.22, "organisation": 0.22,
        "strategie": 0.13, "risques": 0.13,
    },
    "pme": {
        "finance": 0.30, "commercial": 0.20, "organisation": 0.20,
        "strategie": 0.15, "risques": 0.15,
    },
    "croissance": {
        "finance": 0.25, "commercial": 0.25, "organisation": 0.20,
        "strategie": 0.18, "risques": 0.12,
    },
    "reprise": {
        "finance": 0.32, "commercial": 0.25, "organisation": 0.15,
        "strategie": 0.18, "risques": 0.10,
    },
    "strategique": {
        "finance": 0.22, "commercial": 0.18, "organisation": 0.15,
        "strategie": 0.25, "risques": 0.20,
    },
}


# ── Helpers de notation (toujours bornés 0..10) ──────────────────────
def _clamp(value: float, low: float = 0.0, high: float = 10.0) -> float:
    return max(low, min(high, value))


def _score_linear(value: float | None, *, best: float, worst: float) -> float | None:
    """Interpole une note /10 : 10 à ``best``, 0 à ``worst``.

    Fonctionne que ``best`` soit supérieur ou inférieur à ``worst`` (sens
    croissant ou décroissant). Retourne ``None`` si la valeur est absente,
    afin de ne pas pénaliser un KPI non renseigné.
    """
    if value is None:
        return None
    if best == worst:
        return 10.0
    ratio = (value - worst) / (best - worst)
    return round(_clamp(ratio * 10.0), 1)


def _score_scale(value: float | None, *, invert: bool = False) -> float | None:
    """Note une échelle 1..5 sur 10. ``invert=True`` quand 5 = mauvais."""
    if value is None:
        return None
    v = _clamp(value, 1, 5)
    if invert:
        v = 6 - v
    return round((v - 1) / 4 * 10, 1)


def _num(answers: dict[str, Any], key: str) -> float | None:
    """Lit une réponse numérique en tolérant les chaînes / virgules / vides."""
    raw = answers.get(key)
    if raw is None or raw == "":
        return None
    if isinstance(raw, (int, float)):
        return float(raw)
    try:
        return float(str(raw).replace(",", ".").replace(" ", ""))
    except (TypeError, ValueError):
        return None


def _safe_div(num: float | None, den: float | None) -> float | None:
    if num is None or den in (None, 0):
        return None
    return num / den


# ── Calcul des KPIs vitaux ───────────────────────────────────────────
@dataclass
class Kpi:
    key: str
    label: str
    value: float | None
    unit: str
    status: str  # "good" | "warn" | "danger" | "na"
    detail: str = ""

    @property
    def color(self) -> str:
        return {
            "good": "#30d158", "warn": "#ff9f0a",
            "danger": "#ff453a", "na": "#8e8e93",
        }[self.status]

    @property
    def label_status(self) -> str:
        return {
            "good": "Sain", "warn": "À surveiller",
            "danger": "Zone de danger", "na": "Non renseigné",
        }[self.status]


def _status(value: float | None, *, good: float, danger: float,
            higher_is_better: bool) -> str:
    if value is None:
        return "na"
    if higher_is_better:
        if value >= good:
            return "good"
        if value <= danger:
            return "danger"
        return "warn"
    else:
        if value <= good:
            return "good"
        if value >= danger:
            return "danger"
        return "warn"


def compute_kpis(answers: dict[str, Any]) -> dict[str, Kpi]:
    """Calcule les KPIs vitaux dérivés des réponses brutes."""
    ca = _num(answers, "ca_mensuel")
    charges_fixes = _num(answers, "charges_fixes")
    cv_pct = _num(answers, "charges_variables_pct")
    treso = _num(answers, "tresorerie_actuelle")
    enc = _num(answers, "encaissements_30j")
    dec = _num(answers, "decaissements_30j")
    delai = _num(answers, "delai_paiement")
    devis_env = _num(answers, "devis_envoyes")
    devis_sig = _num(answers, "devis_signes")
    dep_client = _num(answers, "part_plus_gros_client")
    recurrent = _num(answers, "ca_recurrent_pct")
    h_trav = _num(answers, "heures_travaillees")
    h_fact = _num(answers, "heures_facturees")
    secours = _num(answers, "tresorerie_secours")

    kpis: dict[str, Kpi] = {}

    # 1. Trésorerie prévisionnelle à 30 jours
    treso_30j = None
    if treso is not None or enc is not None or dec is not None:
        treso_30j = (treso or 0) + (enc or 0) - (dec or 0)
    kpis["treso_30j"] = Kpi(
        "treso_30j", "Trésorerie prévisionnelle à 30 j", treso_30j, "€",
        _status(treso_30j, good=(charges_fixes or 0), danger=0,
                higher_is_better=True) if treso_30j is not None else "na",
        "Solde + encaissements attendus − décaissements certains.",
    )

    # 2. DSO — délai moyen de paiement
    kpis["dso"] = Kpi(
        "dso", "DSO — délai de paiement client", delai, "jours",
        _status(delai, good=30, danger=45, higher_is_better=False),
        "Au-delà de 45 jours, la trésorerie est sous tension.",
    )

    # 3. Marge brute
    marge_pct = (100 - cv_pct) if cv_pct is not None else None
    kpis["marge_brute"] = Kpi(
        "marge_brute", "Taux de marge brute", marge_pct, "%",
        _status(marge_pct, good=50, danger=30, higher_is_better=True),
        "CA restant après les coûts directs.",
    )

    # 4. Couverture des charges fixes (charges fixes / marge brute €)
    couverture = None
    if ca is not None and marge_pct is not None and charges_fixes is not None:
        marge_eur = ca * marge_pct / 100
        couverture = _safe_div(charges_fixes, marge_eur)
        couverture = round(couverture * 100, 1) if couverture is not None else None
    kpis["couverture"] = Kpi(
        "couverture", "Couverture des charges fixes", couverture, "%",
        _status(couverture, good=70, danger=85, higher_is_better=False),
        "Part de la marge brute absorbée par les charges fixes. >85 % = fragile.",
    )

    # 5. Taux de conversion commercial
    conversion = _safe_div(devis_sig, devis_env)
    conversion = round(conversion * 100, 1) if conversion is not None else None
    kpis["conversion"] = Kpi(
        "conversion", "Taux de conversion commercial", conversion, "%",
        _status(conversion, good=33, danger=25, higher_is_better=True),
        "Devis signés / devis envoyés.",
    )

    # 6. Dépendance commerciale (plus gros client)
    kpis["dependance_client"] = Kpi(
        "dependance_client", "Dépendance au plus gros client", dep_client, "%",
        _status(dep_client, good=20, danger=30, higher_is_better=False),
        "Au-delà de 30 %, le risque de perte client devient structurel.",
    )

    # 7. Récurrence du CA
    kpis["recurrence"] = Kpi(
        "recurrence", "Part de CA récurrent", recurrent, "%",
        _status(recurrent, good=30, danger=20, higher_is_better=True),
        "CA prévisible (contrats, abonnements) vs ponctuel.",
    )

    # 8. Capacité facturable
    taux_fact = _safe_div(h_fact, h_trav)
    taux_fact = round(taux_fact * 100, 1) if taux_fact is not None else None
    kpis["capacite_facturable"] = Kpi(
        "capacite_facturable", "Taux d'heures facturables", taux_fact, "%",
        _status(taux_fact, good=55, danger=40, higher_is_better=True),
        "Heures facturées / heures travaillées.",
    )

    # 9. Matelas de trésorerie
    kpis["matelas"] = Kpi(
        "matelas", "Matelas de sécurité", secours, "mois",
        _status(secours, good=3, danger=1, higher_is_better=True),
        "Mois de charges couverts par l'épargne sans aucune rentrée.",
    )

    return kpis


# ── Calcul des scores par domaine ────────────────────────────────────
def _avg(scores: list[float | None]) -> float | None:
    vals = [s for s in scores if s is not None]
    if not vals:
        return None
    return round(sum(vals) / len(vals), 1)


def compute_domain_scores(answers: dict[str, Any],
                          kpis: dict[str, Kpi]) -> dict[str, float | None]:
    """Note chaque domaine /10 à partir des KPIs et réponses brutes."""
    cv_pct = _num(answers, "charges_variables_pct")
    marge_pct = (100 - cv_pct) if cv_pct is not None else None
    charges_fixes = _num(answers, "charges_fixes")
    ca = _num(answers, "ca_mensuel")
    treso_30j = kpis["treso_30j"].value
    couverture = kpis["couverture"].value
    conversion = kpis["conversion"].value
    dep_client = kpis["dependance_client"].value
    recurrent = kpis["recurrence"].value
    taux_fact = kpis["capacite_facturable"].value
    secours = kpis["matelas"].value

    # CAC vs panier moyen
    budget_mkt = _num(answers, "budget_marketing")
    nouveaux = _num(answers, "nouveaux_clients")
    nb_clients = _num(answers, "nb_clients_actifs")
    cac = _safe_div(budget_mkt, nouveaux)
    panier = _safe_div(ca, nb_clients)
    cac_ratio = _safe_div(cac, panier)  # < 1 = sain (récupéré en < 1 mois)

    # ── FINANCE ──────────────────────────────────────────────────────
    treso_score = None
    if treso_30j is not None:
        # 10 si couvre 1 mois de charges, 0 si négatif
        ref = charges_fixes if charges_fixes else (ca or 1)
        treso_score = _score_linear(treso_30j, best=ref, worst=-ref)
    finance = _avg([
        treso_score,
        _score_linear(kpis["dso"].value, best=20, worst=75),
        _score_linear(marge_pct, best=60, worst=20),
        _score_linear(couverture, best=50, worst=100),
    ])

    # ── COMMERCIAL ───────────────────────────────────────────────────
    commercial = _avg([
        _score_linear(conversion, best=50, worst=10),
        _score_linear(dep_client, best=10, worst=60),
        _score_linear(recurrent, best=50, worst=0),
        _score_linear(cac_ratio, best=0.15, worst=1.0) if cac_ratio is not None else None,
    ])

    # ── ORGANISATION ─────────────────────────────────────────────────
    nb_outils = _num(answers, "nb_outils_saas")
    organisation = _avg([
        _score_linear(taux_fact, best=70, worst=20),
        _score_scale(_num(answers, "friction_niveau"), invert=True),
        _score_linear(nb_outils, best=5, worst=25),
        _score_scale(_num(answers, "delegation_niveau")),
    ])

    # ── STRATÉGIE ────────────────────────────────────────────────────
    hausse_map = {"recent": 10.0, "moyen": 7.0, "ancien": 3.0, "jamais": 1.0}
    nb_offres = _num(answers, "nb_offres")
    # Bande idéale d'offres : 2 à 6 → 10 ; pénalise <2 et >10
    offre_score = None
    if nb_offres is not None:
        if 2 <= nb_offres <= 6:
            offre_score = 10.0
        elif nb_offres < 2:
            offre_score = 5.0
        else:
            offre_score = _score_linear(nb_offres, best=6, worst=16)
    marche_map = {"large": 10.0, "limite": 6.0, "etroit": 2.0, "inconnu": 4.0}
    strategie = _avg([
        _score_scale(_num(answers, "pricing_maitrise")),
        _score_scale(_num(answers, "saisonnalite"), invert=True),
        hausse_map.get(answers.get("derniere_hausse_prix")),
        offre_score,
        _score_scale(_num(answers, "vision_3ans")),
        marche_map.get(answers.get("taille_marche")),
    ])

    # ── RISQUES ──────────────────────────────────────────────────────
    dep_fourn = _num(answers, "part_plus_gros_fournisseur")
    part_public = _num(answers, "part_ca_public")
    risques = _avg([
        _score_linear(dep_fourn, best=10, worst=70),
        _score_scale(_num(answers, "exposition_import"), invert=True),
        _score_scale(_num(answers, "homme_cle"), invert=True),
        _score_linear(part_public, best=0, worst=70) if part_public is not None else None,
        _score_linear(secours, best=6, worst=0),
    ])

    return {
        "finance": finance,
        "commercial": commercial,
        "organisation": organisation,
        "strategie": strategie,
        "risques": risques,
    }


# ── Score global pondéré ─────────────────────────────────────────────
def compute_global_score(domain_scores: dict[str, float | None],
                         profile: str) -> int:
    """Moyenne pondérée des domaines /10 → score global /100.

    Renormalise les poids sur les seuls domaines évalués, pour ne pas
    pénaliser un domaine non renseigné.
    """
    weights = DOMAIN_WEIGHTS.get(profile, DOMAIN_WEIGHTS["pme"])
    total_w = 0.0
    acc = 0.0
    for key, score in domain_scores.items():
        if score is None:
            continue
        w = weights.get(key, 0.0)
        acc += score * w
        total_w += w
    if total_w == 0:
        return 0
    return int(round(acc / total_w * 10))


# ── Signaux d'alerte (zones de danger du guide) ──────────────────────
@dataclass
class Signal:
    severity: str  # "critical" | "important" | "watch"
    title: str
    detail: str


SEVERITY_RANK = {"critical": 0, "important": 1, "watch": 2}


def detect_signals(kpis: dict[str, Kpi]) -> list[Signal]:
    """Détecte les signaux d'alerte à partir des KPIs en zone de danger."""
    signals: list[Signal] = []

    def k(key: str) -> Kpi:
        return kpis[key]

    if k("treso_30j").status == "danger":
        signals.append(Signal(
            "critical", "Trésorerie prévisionnelle négative à 30 jours",
            "L'entreprise risque une rupture de liquidités le mois prochain. "
            "Priorité absolue : relancer les encours et étaler les "
            "décaissements.",
        ))
    if k("couverture").status == "danger":
        signals.append(Signal(
            "critical", "Charges fixes trop lourdes face à la marge",
            "Plus de 85 % de la marge brute part dans les charges fixes : la "
            "moindre baisse d'activité fait basculer dans le rouge.",
        ))
    if k("dso").status == "danger":
        signals.append(Signal(
            "important", "Délai de paiement client trop long (DSO élevé)",
            "Les clients paient trop tard : l'entreprise finance leur trésorerie "
            "à sa place. Mettre en place acomptes et relances automatisées.",
        ))
    if k("marge_brute").status == "danger":
        signals.append(Signal(
            "important", "Marge brute insuffisante",
            "La structure de coûts directs laisse trop peu de marge pour "
            "absorber les charges et investir.",
        ))
    if k("conversion").status == "danger":
        signals.append(Signal(
            "important", "Taux de conversion commercial faible",
            "Moins d'un quart des devis aboutit : l'effort commercial se perd. "
            "Revoir le ciblage, le suivi et la présentation des offres.",
        ))
    if k("dependance_client").value is not None and k("dependance_client").value >= 50:
        signals.append(Signal(
            "critical", "Dépendance critique à un client unique",
            "Un seul client pèse la moitié du CA ou plus : sa perte mettrait "
            "l'entreprise en danger immédiat.",
        ))
    elif k("dependance_client").status == "danger":
        signals.append(Signal(
            "important", "Dépendance commerciale élevée",
            "Le plus gros client pèse trop dans le CA. Diversifier le "
            "portefeuille est prioritaire.",
        ))
    if k("recurrence").status == "danger":
        signals.append(Signal(
            "watch", "CA peu récurrent",
            "Le chiffre d'affaires repose surtout sur du ponctuel : chaque mois "
            "doit être reconquis. Développer des offres sous contrat.",
        ))
    if k("capacite_facturable").status == "danger":
        signals.append(Signal(
            "important", "Faible part d'heures facturables",
            "Trop de temps non valorisé (administratif, déplacements, "
            "re-saisies). Automatiser et déléguer le non-facturable.",
        ))
    if k("matelas").status == "danger":
        signals.append(Signal(
            "important", "Matelas de trésorerie insuffisant",
            "Moins d'un mois de charges en réserve : aucun amortisseur en cas "
            "de coup dur.",
        ))

    signals.sort(key=lambda s: SEVERITY_RANK[s.severity])
    return signals


def urgency_level(signals: list[Signal]) -> dict[str, str]:
    """Niveau d'urgence global selon la règle des signaux simultanés."""
    danger_count = sum(1 for s in signals if s.severity in ("critical", "important"))
    if danger_count >= 3:
        return {"level": "urgence", "label": "🚨 Urgence",
                "text": "Plusieurs indicateurs vitaux sont dégradés "
                        "simultanément. Une réunion stratégique est "
                        "recommandée sous 7 jours."}
    if danger_count == 2:
        return {"level": "alerte", "label": "🚨 Alerte",
                "text": "Deux indicateurs vitaux sont dégradés : une action "
                        "prioritaire s'impose."}
    if danger_count == 1:
        return {"level": "avertissement", "label": "⚠️ Avertissement",
                "text": "Un indicateur vital est en zone de danger, à "
                        "surveiller de près."}
    return {"level": "sain", "label": "✅ Sous contrôle",
            "text": "Aucun indicateur vital n'est en zone de danger."}


# ── Plan d'action priorisé ───────────────────────────────────────────
@dataclass
class Recommendation:
    priority: str  # "critique" | "important" | "recommande" | "bonus"
    title: str
    detail: str
    simulateur: str = ""  # slug du simulateur TUS associé (facultatif)


PRIORITY_META = {
    "critique": {"label": "🔴 Critique", "color": "#ff453a",
                 "horizon": "Immédiat"},
    "important": {"label": "🟠 Important", "color": "#ff9f0a",
                  "horizon": "Sous 30 jours"},
    "recommande": {"label": "🟡 Recommandé", "color": "#ffd60a",
                   "horizon": "Sous 90 jours"},
    "bonus": {"label": "🟢 Bonus", "color": "#30d158",
              "horizon": "Quand le reste est en place"},
}
PRIORITY_RANK = {"critique": 0, "important": 1, "recommande": 2, "bonus": 3}


def build_recommendations(answers: dict[str, Any], kpis: dict[str, Kpi],
                          domain_scores: dict[str, float | None],
                          signals: list[Signal]) -> list[Recommendation]:
    """Construit un plan d'action priorisé à partir des signaux et des
    domaines les plus faibles. Chaque reco pointe vers un simulateur TUS
    pertinent quand il existe."""
    recs: list[Recommendation] = []

    sev_to_prio = {"critical": "critique", "important": "important",
                   "watch": "recommande"}
    sim_map = {
        "Trésorerie prévisionnelle négative à 30 jours": "tresorerie",
        "Charges fixes trop lourdes face à la marge": "point_mort",
        "Délai de paiement client trop long (DSO élevé)": "tresorerie",
        "Marge brute insuffisante": "point_mort",
        "Taux de conversion commercial faible": "cac",
        "Dépendance critique à un client unique": "dependance",
        "Dépendance commerciale élevée": "dependance",
        "CA peu récurrent": "retention",
        "Faible part d'heures facturables": "capacite",
        "Matelas de trésorerie insuffisant": "tresorerie",
    }
    for sig in signals:
        recs.append(Recommendation(
            sev_to_prio[sig.severity], sig.title, sig.detail,
            sim_map.get(sig.title, ""),
        ))

    # Renforts basés sur les domaines faibles non déjà couverts
    if (domain_scores.get("organisation") or 10) < 5:
        recs.append(Recommendation(
            "important", "Réduire la friction opérationnelle",
            "Le quotidien est freiné par le chaos et la dispersion des outils. "
            "Cartographier les processus et centraliser les outils.",
            "friction",
        ))
    if (domain_scores.get("strategie") or 10) < 5:
        recs.append(Recommendation(
            "recommande", "Reprendre la main sur le pricing",
            "Les prix sont subis plutôt que pilotés. Tester une grille par "
            "paliers et mesurer l'élasticité.",
            "pricing_paliers",
        ))
    if (domain_scores.get("risques") or 10) < 5:
        recs.append(Recommendation(
            "important", "Sécuriser les approvisionnements et savoir-faire clés",
            "L'exposition aux ruptures (appro importée, personne irremplaçable) "
            "menace la continuité. Diversifier et documenter.",
            "vulnerabilite_fournisseur",
        ))

    hausse = answers.get("derniere_hausse_prix")
    if hausse in ("ancien", "jamais"):
        recs.append(Recommendation(
            "recommande", "Réviser la grille tarifaire",
            "Aucune hausse récente : l'inflation a érodé la marge réelle. "
            "Évaluer une revalorisation maîtrisée.",
            "elasticite",
        ))

    # Toujours proposer un bonus de structuration si rien de critique
    if not any(r.priority == "critique" for r in recs):
        recs.append(Recommendation(
            "bonus", "Chiffrer le coût de l'inaction",
            "Matérialiser ce que coûte le statu quo pour prioriser les "
            "chantiers d'amélioration.",
            "cout_inaction",
        ))

    recs.sort(key=lambda r: PRIORITY_RANK[r.priority])
    return recs


# ── Forces & faiblesses (résumé exécutif) ────────────────────────────
def top_strengths_weaknesses(kpis: dict[str, Kpi],
                             domain_scores: dict[str, float | None],
                             ) -> dict[str, list[str]]:
    """Extrait les 3 forces et 3 faiblesses majeures pour le résumé exécutif."""
    strengths = [k.label for k in kpis.values() if k.status == "good"]
    weaknesses = [k.label for k in kpis.values() if k.status == "danger"]

    # Compléter avec les domaines extrêmes si besoin
    ranked = sorted(
        [(key, s) for key, s in domain_scores.items() if s is not None],
        key=lambda x: x[1], reverse=True,
    )
    for key, s in ranked:
        if s >= 7 and DOMAINS[key].label not in strengths:
            strengths.append(DOMAINS[key].label)
    for key, s in reversed(ranked):
        if s <= 4 and DOMAINS[key].label not in weaknesses:
            weaknesses.append(DOMAINS[key].label)

    return {"strengths": strengths[:3], "weaknesses": weaknesses[:3]}


def verdict_for_score(score: int) -> dict[str, str]:
    """Verdict synthétique associé au score global /100."""
    if score >= 80:
        return {"label": "Solide", "color": "#30d158",
                "text": "L'entreprise repose sur des fondamentaux sains. "
                        "L'enjeu est l'optimisation et la croissance."}
    if score >= 60:
        return {"label": "Sain mais perfectible", "color": "#9acd32",
                "text": "De bonnes bases, avec des chantiers d'amélioration "
                        "ciblés à mener."}
    if score >= 40:
        return {"label": "Fragile", "color": "#ff9f0a",
                "text": "Plusieurs points de vigilance sérieux. Un plan "
                        "d'action structuré est nécessaire."}
    return {"label": "Critique", "color": "#ff453a",
            "text": "Des fondamentaux dégradés exposent l'entreprise. "
                    "Intervention prioritaire requise."}


# ── Orchestration : produit le rapport complet ───────────────────────
def analyze(answers: dict[str, Any], profile: str) -> dict[str, Any]:
    """Point d'entrée : produit le rapport de diagnostic terrain complet.

    Returns un dict sérialisable (stocké dans ``FieldDiagnostic.results``).
    """
    if profile not in PROFILES:
        profile = "pme"

    kpis = compute_kpis(answers)
    domain_scores = compute_domain_scores(answers, kpis)
    global_score = compute_global_score(domain_scores, profile)
    signals = detect_signals(kpis)
    urgency = urgency_level(signals)
    recommendations = build_recommendations(answers, kpis, domain_scores, signals)
    highlights = top_strengths_weaknesses(kpis, domain_scores)
    verdict = verdict_for_score(global_score)

    return {
        "profile": profile,
        "global_score": global_score,
        "verdict": verdict,
        "urgency": urgency,
        "kpis": [
            {
                "key": k.key, "label": k.label, "value": k.value,
                "unit": k.unit, "status": k.status,
                "label_status": k.label_status, "color": k.color,
                "detail": k.detail,
            }
            for k in kpis.values()
        ],
        "domain_scores": [
            {
                "key": key, "label": DOMAINS[key].label,
                "icon": DOMAINS[key].icon, "score": score,
                "weight": DOMAIN_WEIGHTS.get(profile, {}).get(key, 0),
            }
            for key, score in domain_scores.items()
        ],
        "signals": [
            {"severity": s.severity, "title": s.title, "detail": s.detail}
            for s in signals
        ],
        "recommendations": [
            {
                "priority": r.priority,
                "priority_label": PRIORITY_META[r.priority]["label"],
                "priority_color": PRIORITY_META[r.priority]["color"],
                "horizon": PRIORITY_META[r.priority]["horizon"],
                "title": r.title, "detail": r.detail,
                "simulateur": r.simulateur,
            }
            for r in recommendations
        ],
        "highlights": highlights,
    }
