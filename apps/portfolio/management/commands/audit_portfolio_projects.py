"""Audit automatisé des projets portfolio (PageSpeed + Observatory + SSL Labs).

Usage :

    python manage.py audit_portfolio_projects                  # tous les projets publiés avec URL
    python manage.py audit_portfolio_projects --slug netexpress  # un projet précis
    python manage.py audit_portfolio_projects --with-ssl        # inclut le scan SSL Labs (lent)

À planifier en cron Render (1× / semaine suffit pour des sites en prod) :

    0 4 * * 1 python manage.py audit_portfolio_projects --with-ssl
"""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = "Lance l'audit performance/conformité sur les projets portfolio publiés."

    def add_arguments(self, parser):
        parser.add_argument(
            "--slug", default=None,
            help="Limite l'audit à un projet donné (par son slug).",
        )
        parser.add_argument(
            "--no-ssl", action="store_true",
            help="Skip le scan SSL Labs (sinon lancé par défaut, ~60 s par projet).",
        )
        parser.add_argument(
            "--only-missing", action="store_true",
            help=(
                "N'audite que les projets sans résultats automatiques "
                "(remplissage initial rapide, idempotent — idéal en pre-deploy)."
            ),
        )

    def handle(self, *args, **options):
        from apps.portfolio.models import Project
        from apps.portfolio.services.audit import audit_project

        qs = Project.objects.filter(is_published=True).exclude(url="")
        if options["slug"]:
            qs = qs.filter(slug=options["slug"])

        if options["only_missing"]:
            # Un projet est considéré « complet » seulement si CHAQUE catégorie
            # automatique porte sa valeur de référence :
            #   performance/seo/accessibility/security → score
            #   ssl                                    → grade OFFICIEL SSL Labs
            #   security accepte aussi un grade (Observatory) à défaut de score.
            # Le grade SSL provisoire (grade_source="internal") ne suffit PAS :
            # on continue de viser le grade officiel SSL Labs (A+, A…). Une fois
            # tous les indicateurs de référence présents, le projet n'est plus repris.
            required = {
                "performance": "score",
                "seo": "score",
                "accessibility": "score",
                "security": "score",
                "ssl": "grade",
            }
            pending_ids = []
            for proj in qs:
                results = proj.audit_results or {}
                complete = True
                for cat, primary in required.items():
                    node = results.get(cat) or {}
                    has_value = node.get(primary) is not None and node.get(primary) != ""
                    # security : un grade Observatory suffit si pas de score
                    if not has_value and cat == "security":
                        has_value = bool(node.get("grade"))
                    # ssl : exiger le grade OFFICIEL SSL Labs, pas le fallback interne
                    if cat == "ssl" and node.get("grade_source") != "ssllabs":
                        has_value = False
                    if not has_value:
                        complete = False
                        break
                if not complete:
                    pending_ids.append(proj.pk)
            qs = qs.filter(pk__in=pending_ids)

        total = qs.count()
        if total == 0:
            self.stdout.write(self.style.WARNING(
                "[!] Aucun projet à auditer (publié + URL renseignée)."
            ))
            return

        self.stdout.write(self.style.SUCCESS(
            f"[OK] Audit lancé sur {total} projet(s)."
        ))

        for project in qs:
            self.stdout.write(f"\n— {project.title} ({project.url})")
            try:
                audit = audit_project(project.url, include_ssllabs=not options["no_ssl"])
            except Exception as exc:  # noqa: BLE001
                self.stderr.write(self.style.ERROR(f"  [KO] {exc}"))
                continue

            new_results = audit.to_json()
            # Préserve la note UI/UX manuelle (saisie via l'admin) — la pipeline
            # automatisée ne mesure pas l'esthétique / qualité de parcours.
            existing_ui_ux = (project.audit_results or {}).get("ui_ux") or {}
            if existing_ui_ux:
                new_results["ui_ux"] = existing_ui_ux

            project.audit_results = new_results
            project.audit_last_run_at = timezone.now()
            project.save(update_fields=["audit_results", "audit_last_run_at"])

            for cat, score in new_results.items():
                if score.get("score") is not None and score.get("grade"):
                    self.stdout.write(
                        f"   {cat:<16} {score['score']:>3}/100  ·  TLS {score['grade']}"
                    )
                elif score.get("score") is not None:
                    self.stdout.write(f"   {cat:<16} {score['score']:>3}/100")
                elif score.get("grade") is not None:
                    self.stdout.write(f"   {cat:<16} grade {score['grade']}")
                else:
                    self.stdout.write(self.style.WARNING(f"   {cat:<16} (non mesuré)"))

        self.stdout.write(self.style.SUCCESS("\n[OK] Audit terminé."))
