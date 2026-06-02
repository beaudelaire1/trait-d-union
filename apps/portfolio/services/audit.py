"""Audit automatisé de la performance / conformité d'un projet portfolio.

Sources mobilisées (toutes gratuites, toutes officielles) :

- **PageSpeed Insights API** (Google) → 4 scores : performance, seo,
  accessibility, best_practices. Clé API requise : ``PAGESPEED_API_KEY``.
- **Mozilla HTTP Observatory API** → score sécurité (headers HTTP, HTTPS,
  cookies, CSP). Aucune clé.
- **SSL Labs API** → grade SSL/TLS (A+, A, B…). Aucune clé. ⚠️ scan long
  (~60-90 s par site), donc déclenché en mode async côté CLI.

Politique :

- Aucune dépendance dure : si une API échoue, on stocke ``None`` pour la
  catégorie sans casser les autres.
- Idempotent : ``audit_project()`` peut être rappelé sans risque, il
  écrase les anciens scores avec les nouveaux et met à jour ``audit_last_run_at``.
- Pas de blocage tant que le PSI n'est pas configuré : les liens externes
  vers les outils restent disponibles côté template.
"""

from __future__ import annotations

import logging
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional
from urllib.parse import urlparse

from django.conf import settings

logger = logging.getLogger(__name__)


PSI_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
OBSERVATORY_API = "https://observatory-api.mdn.mozilla.net/api/v2/scan"
OBSERVATORY_REPORT = "https://developer.mozilla.org/en-US/observatory/analyze"
SSLLABS_BASE = "https://api.ssllabs.com/api/v3"
DEFAULT_TIMEOUT = 30


# ─── DTO ──────────────────────────────────────────────────────────────
@dataclass
class CategoryScore:
    """Score normalisé d'une catégorie (0-100 pour PSI/Observatory, lettres pour SSL).

    Pour la catégorie ``security``, ``score`` (Observatory 0-100) et ``grade``
    (SSL Labs A+/A/...) cohabitent : c'est l'unique catégorie qui peut porter
    les deux indicateurs simultanément.
    """

    score: Optional[int] = None       # 0-100 (PSI / Observatory)
    grade: Optional[str] = None       # A+, A, B... (SSL Labs)
    measured_at: Optional[str] = None  # ISO 8601
    detail_url: Optional[str] = None   # lien vers le rapport public
    detail_url_secondary: Optional[str] = None  # 2e lien (ex. SSL Labs en complément)

    def as_dict(self) -> dict:
        return {k: v for k, v in asdict(self).items() if v is not None}


@dataclass
class ProjectAudit:
    """Audit complet d'un projet (6 catégories visibles dans le Ch.05).

    Chaque catégorie a son OUTIL DE RÉFÉRENCE :
      - performance  → Google PageSpeed/Lighthouse (score + grade)
      - seo          → Google PageSpeed (score)
      - ui_ux        → note manuelle TUS (score)
      - accessibility→ PageSpeed Lighthouse a11y (score) + lien WAVE
      - security     → Mozilla HTTP Observatory (score)
      - ssl          → SSL Labs (grade A+/A/B…)
    """

    performance: CategoryScore = field(default_factory=CategoryScore)
    seo: CategoryScore = field(default_factory=CategoryScore)
    ui_ux: CategoryScore = field(default_factory=CategoryScore)  # manuel
    accessibility: CategoryScore = field(default_factory=CategoryScore)
    security: CategoryScore = field(default_factory=CategoryScore)  # Observatory
    ssl: CategoryScore = field(default_factory=CategoryScore)       # SSL Labs

    def to_json(self) -> dict:
        return {
            "performance": self.performance.as_dict(),
            "seo": self.seo.as_dict(),
            "ui_ux": self.ui_ux.as_dict(),
            "accessibility": self.accessibility.as_dict(),
            "security": self.security.as_dict(),
            "ssl": self.ssl.as_dict(),
        }


# ─── Backends d'audit ────────────────────────────────────────────────
class _Session:
    """Session HTTP partagée entre tous les appels (keep-alive)."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            try:
                import requests
                cls._instance = requests.Session()
                cls._instance.headers["User-Agent"] = (
                    "TUS-Portfolio-Audit/1.0 (+https://www.traitdunion.it)"
                )
            except ImportError:  # pragma: no cover
                cls._instance = None
        return cls._instance


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _audit_pagespeed(url: str, *, strategy: str = "mobile", runs: int = 3) -> dict[str, CategoryScore]:
    """Renvoie 3 scores Lighthouse : performance, seo, accessibility.

    Outil de référence : Google PageSpeed Insights.
    Stratégie de fiabilisation (Lighthouse a une variance ±5-15 points par run) :

    1. **CrUX d'abord** : si Google publie des Field Data (utilisateurs réels)
       pour la URL, on prend la performance CrUX (28 derniers jours, stable).
    2. **Sinon, médiane sur N runs Lighthouse** (3 par défaut) : on lance
       plusieurs audits et on prend la médiane, ce qui réduit drastiquement
       la variance liée à la charge serveur Google et à la latence réseau.

    ``strategy`` : ``mobile`` (Google priorise la mobile) ou ``desktop``.
    ``runs``     : nombre de runs Lighthouse pour la médiane (3 = bon compromis).
    """
    api_key = getattr(settings, "PAGESPEED_API_KEY", "") or ""
    session = _Session()
    if session is None:
        return {}

    params = {
        "url": url,
        "strategy": strategy,
        "category": ["performance", "seo", "accessibility"],
    }
    if api_key:
        params["key"] = api_key

    report_url = f"https://pagespeed.web.dev/analysis?url={requests_quote(url)}&form_factor={strategy}"

    # ── Run 1 : on regarde si CrUX (Field Data) est disponible ───────
    try:
        resp = session.get(PSI_URL, params=params, timeout=90)
    except Exception as exc:  # noqa: BLE001
        logger.warning("PageSpeed Insights — échec réseau : %s", exc)
        return {}
    if resp.status_code != 200:
        logger.warning("PageSpeed Insights — HTTP %s pour %s", resp.status_code, url)
        return {}

    first_payload = resp.json() or {}
    crux_perf = _extract_crux_performance(first_payload)

    # Lighthouse scores du run 1
    runs_scores: dict[str, list[int]] = {"performance": [], "seo": [], "accessibility": []}
    _accumulate_lh_scores(first_payload, runs_scores)

    # ── Runs 2..N (uniquement si pas de CrUX et runs > 1) ────────────
    if crux_perf is None and runs > 1:
        for _ in range(runs - 1):
            try:
                r = session.get(PSI_URL, params=params, timeout=90)
                if r.status_code == 200:
                    _accumulate_lh_scores(r.json() or {}, runs_scores)
            except Exception:  # noqa: BLE001
                continue  # on tolère une erreur sur un run, on garde les autres

    # ── Construction des scores finaux ───────────────────────────────
    def median(values: list[int]) -> Optional[int]:
        if not values:
            return None
        s = sorted(values)
        return s[len(s) // 2]

    perf_score: Optional[int]
    if crux_perf is not None:
        # Field Data = priorité absolue, ultra-stable.
        perf_score = crux_perf
    else:
        perf_score = median(runs_scores["performance"])
    seo_score = median(runs_scores["seo"])
    a11y_score = median(runs_scores["accessibility"])

    def make(score: Optional[int]) -> CategoryScore:
        if score is None:
            return CategoryScore()
        return CategoryScore(
            score=score,
            measured_at=_now_iso(),
            detail_url=report_url,
        )

    return {
        "performance": make(perf_score),
        "seo": make(seo_score),
        "accessibility": make(a11y_score),
    }


def _accumulate_lh_scores(payload: dict, target: dict[str, list[int]]) -> None:
    """Ajoute les scores Lighthouse d'un payload PSI à la collection."""
    cats = (payload.get("lighthouseResult") or {}).get("categories") or {}
    for cat_key, target_key in (
        ("performance", "performance"),
        ("seo", "seo"),
        ("accessibility", "accessibility"),
    ):
        node = cats.get(cat_key) or {}
        score = node.get("score")
        if isinstance(score, (int, float)):
            target[target_key].append(round(float(score) * 100))


def _extract_crux_performance(payload: dict) -> Optional[int]:
    """Lit le score Performance issu du Chrome User Experience Report (CrUX).

    CrUX agrège les vraies métriques utilisateurs sur 28 jours. C'est ce que
    PSI affiche comme « Field Data » en haut du rapport. Bien plus stable que
    le score Lighthouse en mode lab.

    Renvoie None si Google n'a pas assez de trafic réel sur l'URL pour
    publier un score CrUX (cas fréquent pour les sites à faible audience).
    """
    metrics = (payload.get("loadingExperience") or {}).get("metrics") or {}
    overall = (payload.get("loadingExperience") or {}).get("overall_category")
    if not metrics:
        return None
    # CrUX classe en FAST/AVERAGE/SLOW. On mappe vers un score indicatif
    # uniquement si on a au moins 3 Web Vitals collectés (sinon données trop minces).
    if len(metrics) < 3:
        return None
    mapping = {"FAST": 95, "AVERAGE": 75, "SLOW": 50}
    return mapping.get(overall or "")


def _audit_mozilla_observatory(url: str) -> CategoryScore:
    """Score sécurité via Mozilla HTTP Observatory (API v2).

    Outil de référence : developer.mozilla.org/observatory.
    API v2 : POST déclenche le scan, la réponse contient directement le score
    (``grade`` lettre + ``score`` 0-100+). Le scan est rapide côté v2.
    """
    session = _Session()
    if session is None:
        return CategoryScore()

    hostname = urlparse(url).hostname or ""
    if not hostname:
        return CategoryScore()

    score = None
    grade = None
    report_url = f"{OBSERVATORY_REPORT}?host={hostname}"
    try:
        # API v2 : un seul POST renvoie le résultat (score + grade + details_url).
        resp = session.post(
            OBSERVATORY_API,
            params={"host": hostname},
            timeout=DEFAULT_TIMEOUT,
        )
        if resp.status_code == 200:
            data = resp.json() or {}
            score = data.get("score")
            grade = data.get("grade")
            report_url = data.get("details_url") or report_url
    except Exception as exc:  # noqa: BLE001
        logger.warning("Mozilla Observatory v2 — échec : %s", exc)
        return CategoryScore(detail_url=report_url)

    if not isinstance(score, (int, float)):
        return CategoryScore(detail_url=report_url)

    return CategoryScore(
        score=max(0, min(100, int(score))),  # Observatory peut dépasser 100 (bonus) → on plafonne à 100
        grade=str(grade) if grade else None,
        measured_at=_now_iso(),
        detail_url=report_url,
    )


def _audit_ssllabs(url: str) -> CategoryScore:
    """Grade SSL Labs (A+, A, B…). Pas de clé. Attention : long (~60 s).

    On utilise le mode ``fromCache=on`` pour éviter de refaire un scan complet
    si Labs en a un récent (24-48h).
    """
    session = _Session()
    if session is None:
        return CategoryScore()

    hostname = urlparse(url).hostname or ""
    if not hostname:
        return CategoryScore()

    try:
        for _ in range(8):
            r = session.get(
                f"{SSLLABS_BASE}/analyze",
                params={
                    "host": hostname,
                    "fromCache": "on",
                    "maxAge": 24,
                    "all": "done",
                },
                timeout=DEFAULT_TIMEOUT,
            )
            data = r.json() or {}
            status = data.get("status")
            if status == "READY":
                endpoints = data.get("endpoints") or []
                if endpoints:
                    grade = endpoints[0].get("grade") or endpoints[0].get("gradeTrustIgnored")
                    return CategoryScore(
                        grade=str(grade) if grade else None,
                        measured_at=_now_iso(),
                        detail_url=f"https://www.ssllabs.com/ssltest/analyze.html?d={hostname}",
                    )
                break
            if status == "ERROR":
                break
            time.sleep(8)
    except Exception as exc:  # noqa: BLE001
        logger.warning("SSL Labs — échec : %s", exc)
    return CategoryScore()


# ─── Moteur interne TUS (zéro API, zéro quota) ───────────────────────
def _audit_internal_engine(url: str) -> dict[str, CategoryScore]:
    """Calcule perf/SEO/accessibilité/sécurité depuis l'URL via le moteur
    interne ``apps.diagnostic.service.run_diagnostic``.

    Avantage : AUCUNE dépendance externe, AUCUN quota, toujours disponible.
    C'est le socle de mesure. Les grades officiels (Observatory, SSL Labs)
    viennent l'enrichir ensuite quand ils répondent.

    Le moteur renvoie par catégorie : {label, score, max, percent, items}.
    On convertit ``percent`` (0-100) en notre CategoryScore.
    """
    try:
        from apps.diagnostic.service import run_diagnostic
    except Exception as exc:  # noqa: BLE001
        logger.warning("Moteur interne indisponible : %s", exc)
        return {}

    try:
        report = run_diagnostic(url)
    except Exception as exc:  # noqa: BLE001
        logger.warning("run_diagnostic a échoué pour %s : %s", url, exc)
        return {}

    cats = report.get("categories") or {}
    out: dict[str, CategoryScore] = {}
    # mapping nom interne → clé portfolio
    for internal_key, portfolio_key in (
        ("performance", "performance"),
        ("seo", "seo"),
        ("accessibilite", "accessibility"),
        ("securite", "security"),
        ("ssl", "ssl"),
    ):
        node = cats.get(internal_key)
        if not node:
            continue
        percent = node.get("percent")
        if isinstance(percent, (int, float)):
            out[portfolio_key] = CategoryScore(
                score=int(percent),
                measured_at=_now_iso(),
            )
    return out


def requests_quote(value: str) -> str:
    """Helper léger pour quoter une URL sans dépendre de requests à l'import."""
    from urllib.parse import quote
    return quote(value, safe="")


def _ssl_grade_from_score(score: Optional[int]) -> Optional[str]:
    """Dérive un grade SSL provisoire à partir du score du moteur interne.

    Le socle interne réalise une vraie poignée de main TLS sur l'URL du projet
    (certificat valide, expiration > 30 j, protocole TLS 1.2/1.3). On en tire
    un grade conservateur — on ne vérifie ni les ciphers ni HSTS comme SSL Labs,
    donc on plafonne volontairement à « A » (jamais « A+ »). SSL Labs écrase
    ensuite ce grade par la note officielle (A+, A, B…) via le cron.
    """
    if score is None:
        return None
    if score >= 100:
        return "A"
    if score >= 80:
        return "A-"
    if score >= 60:
        return "B"
    if score >= 40:
        return "C"
    if score >= 20:
        return "D"
    return "F"


# ─── Pipeline ────────────────────────────────────────────────────────
def audit_project(
    url: str,
    *,
    include_ssllabs: bool = True,
) -> ProjectAudit:
    """Lance tous les audits depuis l'URL et retourne un ``ProjectAudit``.

    Stratégie en 3 couches, du plus fiable au plus optionnel :

    1. **Moteur interne TUS** (socle) — perf, SEO, accessibilité, sécurité,
       SSL calculés directement depuis l'URL. Aucun quota, toujours dispo.
    2. **Grades officiels** — Mozilla Observatory (sécurité A+) et SSL Labs
       (chiffrement A+) écrasent/enrichissent le socle s'ils répondent.
    3. **PageSpeed** (bonus) — si ``PAGESPEED_API_KEY`` configurée, la médiane
       Lighthouse remplace le socle pour perf/SEO/accessibilité (plus précis).

    Résultat : toutes les cartes ont un score ET un lien « Tester », même
    sans aucune clé API configurée.
    """
    audit = ProjectAudit()
    if not url:
        return audit

    hostname = urlparse(url).hostname or ""

    # ── Couche 1 : socle interne (toujours) ──────────────────────────
    internal = _audit_internal_engine(url)
    audit.performance = internal.get("performance", CategoryScore())
    audit.seo = internal.get("seo", CategoryScore())
    audit.accessibility = internal.get("accessibility", CategoryScore())
    audit.security = internal.get("security", CategoryScore())
    audit.ssl = internal.get("ssl", CategoryScore())

    # ── Couche 2 : grades officiels (enrichissement) ─────────────────
    # Sécurité — Mozilla Observatory (grade + score précis).
    obs = _audit_mozilla_observatory(url)
    if obs.score is not None or obs.grade:
        audit.security = obs
    elif audit.security.score is not None and not audit.security.detail_url:
        # Garder le socle mais ajouter le lien Tester Observatory.
        audit.security.detail_url = f"{OBSERVATORY_REPORT}?host={hostname}"

    # SSL/TLS — SSL Labs (grade officiel A+/A/B…).
    if include_ssllabs:
        ssl = _audit_ssllabs(url)
        if ssl.grade:
            audit.ssl = ssl
    # Si SSL Labs n'a pas (encore) répondu, on garantit un grade provisoire
    # honnête dérivé de la poignée de main TLS du moteur interne. SSL Labs
    # écrasera ce grade par la note officielle au prochain passage du cron.
    if not audit.ssl.grade:
        fallback_grade = _ssl_grade_from_score(audit.ssl.score)
        if fallback_grade:
            audit.ssl.grade = fallback_grade
            if not audit.ssl.measured_at:
                audit.ssl.measured_at = _now_iso()
    # Toujours garantir un lien Tester SSL Labs.
    if hostname and not audit.ssl.detail_url:
        audit.ssl.detail_url = f"https://www.ssllabs.com/ssltest/analyze.html?d={hostname}"

    # ── Couche 3 : PageSpeed bonus (si clé configurée) ───────────────
    if getattr(settings, "PAGESPEED_API_KEY", ""):
        psi = _audit_pagespeed(url)
        if psi.get("performance") and psi["performance"].score is not None:
            audit.performance = psi["performance"]
        if psi.get("seo") and psi["seo"].score is not None:
            audit.seo = psi["seo"]
        if psi.get("accessibility") and psi["accessibility"].score is not None:
            audit.accessibility = psi["accessibility"]

    # ── Garantir un lien « Tester » sur chaque carte automatique ─────
    encoded = requests_quote(url)
    psi_link = f"https://pagespeed.web.dev/analysis?url={encoded}&form_factor=mobile"
    if not audit.performance.detail_url:
        audit.performance.detail_url = psi_link
    if not audit.seo.detail_url:
        audit.seo.detail_url = psi_link
    if not audit.accessibility.detail_url:
        audit.accessibility.detail_url = f"https://wave.webaim.org/report#/{url}"

    return audit


__all__ = [
    "CategoryScore",
    "ProjectAudit",
    "audit_project",
]
