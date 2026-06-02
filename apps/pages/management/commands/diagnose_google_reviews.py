"""Diagnostic complet de la chaîne Google Reviews → Testimonial → Home.

Usage :
    python manage.py diagnose_google_reviews

Vérifie en cascade :
  1. Settings GOOGLE_REVIEWS (clé / place_id présents ?)
  2. Appel HTTP brut à Places API (status, message d'erreur)
  3. Nombre d'avis bruts retournés par Google
  4. Détail de chaque avis (note, longueur, langue, auteur)
  5. État de la table Testimonial (combien total, combien Google, combien publiés)
  6. Cache homepage_testimonials (présent ? quel contenu ?)
  7. Politique de publication automatique (rating >= min_rating ?)

Sort un rapport humain qui pointe directement la cause du blocage.
Aucun secret n'est affiché en clair.
"""

from __future__ import annotations

from django.conf import settings
from django.core.cache import cache
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Diagnostic complet de la synchronisation Google Reviews."

    def add_arguments(self, parser):
        parser.add_argument(
            "--min-rating", type=int, default=4,
            help="Note minimale utilisée pour la publication auto (info, défaut 4).",
        )

    def handle(self, *args, **options):
        from apps.pages.models import Testimonial, TestimonialSource

        self._h("1. CONFIGURATION (settings.GOOGLE_REVIEWS)")
        cfg = getattr(settings, "GOOGLE_REVIEWS", {}) or {}
        api_key = cfg.get("API_KEY", "")
        place_id = cfg.get("PLACE_ID", "")
        language = cfg.get("LANGUAGE", "fr")

        self._kv("API_KEY", self._mask(api_key))
        self._kv("PLACE_ID", place_id or "(vide)")
        self._kv("LANGUAGE", language)

        if not api_key:
            self._fail(
                "API_KEY vide → la synchro ne peut pas tourner.\n"
                "       Renseigne GOOGLE_PLACES_API_KEY dans le .env (local) "
                "ou dans Render → Environment (prod)."
            )
            return
        if not place_id:
            self._fail(
                "PLACE_ID vide → impossible d'identifier ta fiche Google Business.\n"
                "       Renseigne GOOGLE_PLACE_ID."
            )
            return
        self._ok("Configuration OK")

        # ─── 2. Appel HTTP brut ─────────────────────────────────────
        self._h("2. APPEL HTTP — Places API (New)")
        try:
            import requests
        except ImportError:
            self._fail("Le package `requests` est manquant.")
            return

        url = f"https://places.googleapis.com/v1/places/{place_id}"
        headers = {
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": "id,displayName,rating,userRatingCount,reviews",
            "Accept-Language": language,
        }
        try:
            resp = requests.get(url, headers=headers, params={"languageCode": language}, timeout=15)
        except Exception as exc:  # noqa: BLE001
            self._fail(f"Erreur réseau : {exc}")
            return

        self._kv("HTTP status", resp.status_code)

        if resp.status_code == 401 or resp.status_code == 403:
            self._fail(
                f"Google a refusé la clé (HTTP {resp.status_code}).\n"
                "       Causes fréquentes :\n"
                "       - L'API 'Places API (New)' n'est pas activée dans le projet Google Cloud.\n"
                "       - La clé a une restriction d'IP qui ne couvre pas l'IP appelante.\n"
                "       - La clé a une restriction de referrer HTTP qui bloque les appels serveur."
            )
            self._kv("Réponse", resp.text[:300])
            return
        if resp.status_code == 404:
            self._fail(
                f"place_id introuvable côté Google : {place_id!r}.\n"
                "       Vérifie l'ID sur https://developers.google.com/maps/documentation/places/web-service/place-id"
            )
            return
        if resp.status_code >= 400:
            self._fail(f"HTTP {resp.status_code} : {resp.text[:300]}")
            return

        try:
            payload = resp.json() or {}
        except ValueError:
            self._fail("Réponse JSON invalide.")
            return

        self._ok("API a répondu sans erreur")

        # ─── 3. Contenu remonté ─────────────────────────────────────
        self._h("3. AVIS REMONTÉS PAR GOOGLE")
        place_name = (payload.get("displayName") or {}).get("text", "?")
        global_rating = payload.get("rating", "?")
        rating_count = payload.get("userRatingCount", "?")
        reviews = payload.get("reviews", []) or []

        self._kv("Fiche Google", place_name)
        self._kv("Note moyenne", f"{global_rating} ({rating_count} avis au total)")
        self._kv("Avis renvoyés par l'API", f"{len(reviews)} (limite Google : 5 max)")

        if not reviews:
            self._warn(
                "Google ne renvoie AUCUN avis pour cette fiche.\n"
                "       Causes possibles :\n"
                "       - Aucun avis n'a encore été laissé sur ta fiche.\n"
                "       - La fiche est trop récente / pas encore validée.\n"
                "       - La fiche a un statut spécifique (établissement fermé, etc.)."
            )
            return

        min_rating = options["min_rating"]
        for i, r in enumerate(reviews, 1):
            author = (r.get("authorAttribution") or {}).get("displayName", "?")
            rating = r.get("rating", 0)
            text = (r.get("text") or {}).get("text", "") or (r.get("originalText") or {}).get("text", "")
            text_short = (text[:90] + "…") if len(text) > 90 else text
            published = r.get("publishTime", "?")
            auto_pub = "auto-publié" if rating >= min_rating else f"DRAFT (note < {min_rating})"
            self.stdout.write(
                f"  [{i}] {author} ({rating}/5) [{auto_pub}] · {published}\n"
                f"      → {text_short!r}"
            )

        # ─── 4. Etat BDD ────────────────────────────────────────────
        self._h("4. TABLE Testimonial")
        total = Testimonial.objects.count()
        manual = Testimonial.objects.filter(source=TestimonialSource.MANUAL).count()
        google = Testimonial.objects.filter(source=TestimonialSource.GOOGLE).count()
        published = Testimonial.objects.filter(is_published=True).count()
        google_published = Testimonial.objects.filter(
            source=TestimonialSource.GOOGLE, is_published=True
        ).count()

        self._kv("Total en base", total)
        self._kv("  → manuels", manual)
        self._kv("  → Google", google)
        self._kv("Publiés (visibles sur la home)", published)
        self._kv("  → Google publiés", google_published)

        if google == 0 and reviews:
            self._warn(
                "L'API renvoie des avis MAIS rien n'est en base — la synchro n'a jamais tourné.\n"
                "       Lance maintenant :\n"
                "       python manage.py sync_google_reviews"
            )
        elif google > 0 and google_published == 0:
            self._warn(
                "Des avis Google sont en base mais AUCUN n'est publié.\n"
                "       Ils ont probablement une note < 4. Va dans /admin/ → Témoignages\n"
                "       et coche 'is_published' manuellement, ou relance avec --min-rating 1."
            )

        # ─── 5. Cache home ──────────────────────────────────────────
        self._h("5. CACHE 'homepage_testimonials'")
        cached = cache.get("homepage_testimonials")
        if cached is None:
            self._ok("Cache vide → la prochaine vue régénérera la liste.")
        else:
            n_items = len(cached.get("items", [])) if isinstance(cached, dict) else 0
            self._kv("Items en cache", n_items)
            self._warn(
                "Si tu viens de modifier des témoignages et que la home n'a pas suivi,\n"
                "       force l'invalidation : python manage.py shell -c \""
                "from django.core.cache import cache; cache.delete('homepage_testimonials')\""
            )

        self._h("RÉSUMÉ")
        if reviews and google_published > 0:
            self._ok("Tout est en ordre : %d avis Google publiés sur la home." % google_published)
        elif reviews and google_published == 0:
            self._warn("API OK mais 0 avis publié — voir bloc 4 ci-dessus.")
        elif not reviews:
            self._warn("API ne renvoie aucun avis pour cette fiche.")

    # ─── helpers UI ────────────────────────────────────────────────
    def _h(self, title: str):
        self.stdout.write("\n" + self.style.MIGRATE_HEADING(f"== {title} =="))

    def _kv(self, k, v):
        self.stdout.write(f"  {k:<32} {v}")

    def _ok(self, msg: str):
        self.stdout.write(self.style.SUCCESS(f"  [OK] {msg}"))

    def _warn(self, msg: str):
        self.stdout.write(self.style.WARNING(f"  [!]  {msg}"))

    def _fail(self, msg: str):
        self.stderr.write(self.style.ERROR(f"  [KO] {msg}"))

    @staticmethod
    def _mask(value: str) -> str:
        if not value:
            return "(vide)"
        if len(value) <= 8:
            return "*" * len(value)
        return f"{value[:4]}…{value[-2:]} (len={len(value)})"
