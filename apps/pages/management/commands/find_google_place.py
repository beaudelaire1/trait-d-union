"""Recherche un place_id par requête texte via Places API (Text Search).

Utile quand le place_id configuré ne renvoie pas d'avis : il pointe peut-être
sur un "lieu Maps" et non sur une "Business Profile". Cette commande liste
tous les `place_id` matchant ton nom et leur compteur d'avis pour t'aider à
choisir le bon.

Usage :

    python manage.py find_google_place "Trait d'Union Studio Cayenne"
    python manage.py find_google_place "Trait d'Union Studio" --region fr
"""

from __future__ import annotations

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Cherche un place_id par requête texte (Places API Text Search)."

    def add_arguments(self, parser):
        parser.add_argument("query", help="Texte à rechercher (ex. 'Trait d'Union Studio Cayenne').")
        parser.add_argument("--region", default="fr", help="Code pays (défaut : fr).")
        parser.add_argument("--language", default="fr", help="Code langue (défaut : fr).")

    def handle(self, *args, **options):
        cfg = getattr(settings, "GOOGLE_REVIEWS", {}) or {}
        api_key = cfg.get("API_KEY", "")
        if not api_key:
            self.stderr.write(self.style.ERROR(
                "[KO] GOOGLE_PLACES_API_KEY manquant. Renseigne-le dans .env."
            ))
            return

        try:
            import requests
        except ImportError:
            self.stderr.write(self.style.ERROR("[KO] Le package `requests` est manquant."))
            return

        url = "https://places.googleapis.com/v1/places:searchText"
        headers = {
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": (
                "places.id,places.displayName,places.formattedAddress,"
                "places.rating,places.userRatingCount,places.businessStatus"
            ),
            "Content-Type": "application/json",
        }
        body = {
            "textQuery": options["query"],
            "languageCode": options["language"],
            "regionCode": options["region"].upper(),
        }

        try:
            resp = requests.post(url, headers=headers, json=body, timeout=15)
        except Exception as exc:  # noqa: BLE001
            self.stderr.write(self.style.ERROR(f"[KO] Erreur reseau : {exc}"))
            return

        if resp.status_code >= 400:
            self.stderr.write(self.style.ERROR(
                f"[KO] HTTP {resp.status_code} : {resp.text[:300]}"
            ))
            return

        payload = resp.json() or {}
        places = payload.get("places", []) or []

        if not places:
            self.stdout.write(self.style.WARNING(
                f"[!] Aucun resultat pour : {options['query']!r}"
            ))
            return

        self.stdout.write(self.style.SUCCESS(
            f"[OK] {len(places)} resultat(s) pour : {options['query']!r}\n"
        ))
        configured = cfg.get("PLACE_ID", "")

        for i, p in enumerate(places, 1):
            name = (p.get("displayName") or {}).get("text", "?")
            place_id = p.get("id", "?")
            address = p.get("formattedAddress", "?")
            rating = p.get("rating", "(aucun)")
            count = p.get("userRatingCount", 0)
            status = p.get("businessStatus", "?")
            marker = "  <- PLACE_ID actuellement configure" if place_id == configured else ""

            self.stdout.write(f"[{i}] {name}{marker}")
            self.stdout.write(f"    place_id : {place_id}")
            self.stdout.write(f"    adresse  : {address}")
            self.stdout.write(f"    note     : {rating} ({count} avis)")
            self.stdout.write(f"    statut   : {status}")
            self.stdout.write("")

        # Conseil
        configured_match = next((p for p in places if p.get("id") == configured), None)
        best = max(places, key=lambda p: p.get("userRatingCount", 0) or 0)
        if best.get("userRatingCount", 0) and best.get("id") != configured:
            self.stdout.write(self.style.WARNING(
                "Suggestion : le place_id avec le plus d'avis n'est PAS celui configure.\n"
                f"  Mets a jour ton .env avec : GOOGLE_PLACE_ID={best.get('id')}\n"
                f"  ({best.get('userRatingCount')} avis sur cette fiche)."
            ))
        elif configured_match and not configured_match.get("userRatingCount"):
            self.stdout.write(self.style.WARNING(
                "Le place_id configure existe mais Google n'y associe AUCUN avis.\n"
                "  Verifie sur business.google.com que ta fiche est validee."
            ))
