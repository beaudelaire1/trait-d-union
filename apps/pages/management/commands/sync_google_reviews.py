"""Synchronisation des avis Google Business Profile dans la table Testimonial.

Usage :

    python manage.py sync_google_reviews                  # synchro normale
    python manage.py sync_google_reviews --dry-run        # sans écrire en BDD
    python manage.py sync_google_reviews --min-rating 5   # ne publier que les 5/5
    python manage.py sync_google_reviews --no-auto-publish  # tous restent draft

À planifier en cron / django-q (ex. toutes les 6 h en prod) :

    0 */6 * * * python manage.py sync_google_reviews
"""

from __future__ import annotations

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Synchronise les avis Google (Places API) avec les Testimonial."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Affiche les avis trouvés sans les écrire en BDD.",
        )
        parser.add_argument(
            "--min-rating", type=int, default=4,
            help="Note minimale pour publier automatiquement un avis (défaut : 4/5).",
        )
        parser.add_argument(
            "--no-auto-publish", action="store_true",
            help="Crée tous les avis avec is_published=False (modération manuelle).",
        )

    def handle(self, *args, **options):
        from apps.pages.services.google_reviews import (
            GooglePlacesBackend,
            sync_google_reviews,
        )

        if options["dry_run"]:
            backend = GooglePlacesBackend()
            try:
                reviews = backend.fetch_reviews()
            except Exception as exc:  # noqa: BLE001
                self.stderr.write(self.style.ERROR(f"[KO] {exc}"))
                return
            self.stdout.write(self.style.SUCCESS(f"[OK] {len(reviews)} avis trouvés (dry-run)."))
            for r in reviews:
                self.stdout.write(
                    f"  - {r['author_name']} ({r['rating']}/5) — "
                    f"{(r['content'][:80] + '…') if len(r['content']) > 80 else r['content']}"
                )
            return

        result = sync_google_reviews(
            auto_publish=not options["no_auto_publish"],
            min_rating=options["min_rating"],
        )

        if result.errors:
            for err in result.errors:
                self.stderr.write(self.style.WARNING(f"  [WARN] {err}"))

        self.stdout.write(self.style.SUCCESS(
            f"[OK] Google Reviews — fetched={result.fetched}, "
            f"created={result.created}, updated={result.updated}, skipped={result.skipped}"
        ))
