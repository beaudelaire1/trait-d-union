"""Synchronisation des avis Google Business → modèle Testimonial.

Backend par défaut : **Google Places API (New)** — `places.googleapis.com/v1`.
Limites connues :
- 5 avis maximum retournés par place (limite Google, pas négociable côté API publique).
- Champ `reviews` exigé dans le ``X-Goog-FieldMask``.
- Authentification : clé API simple (référence ``GOOGLE_PLACES_API_KEY``).

Pour dépasser 5 avis, il faut migrer vers **Business Profile API** (validation
manuelle Google + OAuth utilisateur). L'interface ``GoogleReviewsBackend`` ci-
dessous est conçue pour qu'on puisse ajouter un second backend sans toucher au
métier (commande Django, modèle, vues).

Usage métier :

    from apps.pages.services.google_reviews import sync_google_reviews
    result = sync_google_reviews()  # créé + mis à jour les Testimonial
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable, Optional

from django.conf import settings
from django.utils.dateparse import parse_datetime

logger = logging.getLogger(__name__)


PLACES_BASE_URL = "https://places.googleapis.com/v1"
DEFAULT_TIMEOUT = 12
DEFAULT_FIELD_MASK = "id,displayName,rating,userRatingCount,reviews"


# ─── Exceptions ───────────────────────────────────────────────────────
class GoogleReviewsError(Exception):
    """Erreur générique de la couche synchronisation Google Reviews."""


class GoogleReviewsConfigError(GoogleReviewsError):
    """Clé API ou place_id manquant / invalide."""


class GoogleReviewsTransportError(GoogleReviewsError):
    """Échec réseau ou statut HTTP non récupérable."""


# ─── Résultat de synchro ──────────────────────────────────────────────
@dataclass
class SyncResult:
    fetched: int = 0
    created: int = 0
    updated: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "fetched": self.fetched,
            "created": self.created,
            "updated": self.updated,
            "skipped": self.skipped,
            "errors": self.errors,
        }


# ─── Backend : Google Places API ──────────────────────────────────────
class GooglePlacesBackend:
    """Implémentation Places API (New).

    Méthode publique unique : :meth:`fetch_reviews()` qui retourne une liste de
    dicts normalisés indépendants du modèle Django :

        {
          "external_id": str,
          "author_name": str,
          "rating": int,
          "content": str,
          "avatar_url": str,
          "review_url": str,
          "published_at": datetime | None,
          "raw": dict,  # payload brut, pour debug
        }
    """

    def __init__(
        self,
        *,
        api_key: Optional[str] = None,
        place_id: Optional[str] = None,
        language: str = "fr",
        timeout: int = DEFAULT_TIMEOUT,
    ) -> None:
        cfg = getattr(settings, "GOOGLE_REVIEWS", {}) or {}
        self.api_key = api_key or cfg.get("API_KEY", "")
        self.place_id = place_id or cfg.get("PLACE_ID", "")
        self.language = language or cfg.get("LANGUAGE", "fr")
        self.timeout = timeout

    # ── Validation ───────────────────────────────────────────────────
    def _ensure_config(self) -> None:
        if not self.api_key:
            raise GoogleReviewsConfigError(
                "GOOGLE_REVIEWS['API_KEY'] manquant. "
                "Crée une clé dans Google Cloud Console (API Places enabled)."
            )
        if not self.place_id:
            raise GoogleReviewsConfigError(
                "GOOGLE_REVIEWS['PLACE_ID'] manquant. "
                "Récupère ton place_id sur https://developers.google.com/maps/documentation/places/web-service/place-id"
            )

    # ── Appel HTTP ───────────────────────────────────────────────────
    def fetch_reviews(self) -> list[dict[str, Any]]:
        self._ensure_config()
        try:
            import requests
        except ImportError as exc:  # pragma: no cover
            raise GoogleReviewsTransportError(
                "Le package `requests` est requis pour la synchro Google Reviews."
            ) from exc

        url = f"{PLACES_BASE_URL}/places/{self.place_id}"
        headers = {
            "X-Goog-Api-Key": self.api_key,
            "X-Goog-FieldMask": DEFAULT_FIELD_MASK,
            "Accept-Language": self.language,
        }
        params = {"languageCode": self.language}

        try:
            resp = requests.get(url, headers=headers, params=params, timeout=self.timeout)
        except Exception as exc:  # noqa: BLE001
            raise GoogleReviewsTransportError(
                f"Échec réseau Places API : {exc}"
            ) from exc

        if resp.status_code in (401, 403):
            raise GoogleReviewsConfigError(
                f"Places API a refusé la clé ou les permissions (HTTP {resp.status_code}). "
                "Vérifie que l'API Places (New) est activée et que la clé est valide."
            )
        if resp.status_code == 404:
            raise GoogleReviewsConfigError(
                f"place_id introuvable côté Google ({self.place_id!r})."
            )
        if resp.status_code >= 400:
            raise GoogleReviewsTransportError(
                f"Places API a renvoyé HTTP {resp.status_code}."
            )

        try:
            payload = resp.json() or {}
        except ValueError as exc:
            raise GoogleReviewsTransportError(
                "Places API a renvoyé un JSON invalide."
            ) from exc

        return [self._normalize(r) for r in payload.get("reviews", []) if isinstance(r, dict)]

    # ── Normalisation ────────────────────────────────────────────────
    @staticmethod
    def _normalize(review: dict[str, Any]) -> dict[str, Any]:
        text_node = review.get("text") or review.get("originalText") or {}
        author_node = review.get("authorAttribution") or {}
        published_raw = review.get("publishTime") or review.get("publishedTime")
        published_at = None
        if published_raw:
            published_at = parse_datetime(str(published_raw))
            if published_at and published_at.tzinfo is None:
                published_at = published_at.replace(tzinfo=timezone.utc)

        rating = review.get("rating")
        try:
            rating_int = int(round(float(rating))) if rating is not None else 5
        except (TypeError, ValueError):
            rating_int = 5
        rating_int = max(1, min(5, rating_int))

        return {
            "external_id": str(review.get("name") or review.get("reviewId") or ""),
            "author_name": author_node.get("displayName") or "Client Google",
            "rating": rating_int,
            "content": (text_node.get("text") if isinstance(text_node, dict) else str(text_node)) or "",
            "avatar_url": author_node.get("photoUri") or "",
            "review_url": review.get("googleMapsUri") or author_node.get("uri") or "",
            "published_at": published_at,
            "raw": review,
        }


# ─── Pipeline d'ingestion ────────────────────────────────────────────
def sync_google_reviews(
    *,
    backend: Optional[GooglePlacesBackend] = None,
    auto_publish: bool = True,
    min_rating: int = 4,
    skip_empty: bool = True,
) -> SyncResult:
    """UPSERT les avis Google dans la table ``Testimonial``.

    Politique éditoriale par défaut :

    - on ne publie automatiquement que les avis ``rating >= min_rating`` (4 par
      défaut) — un avis 1/5 n'apparaîtra pas sur la home tant qu'un humain ne
      l'a pas explicitement validé dans l'admin ;
    - les avis sans contenu textuel sont ignorés (``skip_empty=True``).

    L'admin reste maître du final : ``is_published`` et ``order`` posés en BDD
    ne sont **jamais** écrasés par la synchro après la première création.
    """
    from apps.pages.models import Testimonial, TestimonialSource

    result = SyncResult()
    backend = backend or GooglePlacesBackend()
    try:
        reviews = backend.fetch_reviews()
    except GoogleReviewsConfigError as exc:
        logger.warning("Synchro Google Reviews ignorée : %s", exc)
        result.errors.append(str(exc))
        return result
    except GoogleReviewsError as exc:
        logger.exception("Échec synchro Google Reviews")
        result.errors.append(str(exc))
        return result

    result.fetched = len(reviews)
    now = datetime.now(timezone.utc)

    for r in reviews:
        if not r.get("external_id"):
            result.skipped += 1
            continue
        if skip_empty and not (r.get("content") or "").strip():
            result.skipped += 1
            continue

        existing = Testimonial.objects.filter(google_review_id=r["external_id"]).first()
        if existing is None:
            # Création : on respecte la politique de publication automatique
            should_publish = auto_publish and r["rating"] >= min_rating
            Testimonial.objects.create(
                client_name=r["author_name"][:200],
                content=r["content"][:5000],
                rating=r["rating"],
                avatar_url=r["avatar_url"][:500] if r.get("avatar_url") else "",
                review_url=r["review_url"][:500] if r.get("review_url") else "",
                review_published_at=r.get("published_at"),
                source=TestimonialSource.GOOGLE,
                google_review_id=r["external_id"][:255],
                is_published=should_publish,
                last_synced_at=now,
            )
            result.created += 1
        else:
            # Update : on rafraîchit le contenu mais on NE TOUCHE PAS à
            # is_published / order qui restent pilotés par l'admin.
            Testimonial.objects.filter(pk=existing.pk).update(
                client_name=r["author_name"][:200],
                content=r["content"][:5000],
                rating=r["rating"],
                avatar_url=r["avatar_url"][:500] if r.get("avatar_url") else "",
                review_url=r["review_url"][:500] if r.get("review_url") else "",
                review_published_at=r.get("published_at"),
                last_synced_at=now,
            )
            result.updated += 1

    # Invalidation du cache home pour qu'un refresh affiche les nouveaux avis
    try:
        from django.core.cache import cache
        cache.delete("homepage_testimonials")
    except Exception:  # pragma: no cover
        pass

    return result


__all__ = [
    "GooglePlacesBackend",
    "GoogleReviewsError",
    "GoogleReviewsConfigError",
    "GoogleReviewsTransportError",
    "SyncResult",
    "sync_google_reviews",
]
