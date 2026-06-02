"""Insère un projet portfolio « TitanTech » de démo, en local.

Usage :
    python manage.py seed_titantech            # créé / met à jour
    python manage.py seed_titantech --clear    # supprime le projet de démo

Le projet pointe sur https://www.traitdunion.it pour pouvoir tester le Ch.05
(audit performance) sur un vrai site en ligne.

Idempotent : la commande s'appuie sur le slug ``titantech``. Relancée, elle
met à jour les contenus sans créer de doublon ; ``--clear`` supprime
proprement (et avec lui les phases de stratégie en cascade).
"""

from __future__ import annotations

from datetime import datetime, timezone

from django.core.management.base import BaseCommand


SLUG = "titantech"
PROJECT_URL = "https://www.traitdunion.it"


class Command(BaseCommand):
    help = "Crée (ou met à jour) un projet portfolio « TitanTech » de démo."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear", action="store_true",
            help="Supprime le projet de démo (et ses phases / images).",
        )

    def handle(self, *args, **options):
        from apps.portfolio.models import (
            Project,
            ProjectType,
            StrategyPhase,
            StrategyPhaseIcon,
        )

        if options["clear"]:
            qs = Project.objects.filter(slug=SLUG)
            count = qs.count()
            qs.delete()
            self.stdout.write(self.style.SUCCESS(
                f"[OK] {count} projet(s) supprimé(s) (slug={SLUG!r})."
            ))
            return

        # ── Identité projet ──────────────────────────────────────────
        defaults = dict(
            title="TitanTech",
            project_type=ProjectType.OUTILS,
            client_name="TitanTech Industries",
            url=PROJECT_URL,
            objective=(
                "<p>TitanTech opère depuis 12 ans dans la maintenance industrielle "
                "en Outre-mer. Son équipe est dispersée sur trois îles, ses devis "
                "se perdent entre messageries et fichiers Excel, et chaque demande "
                "client demande une coordination manuelle qui pèse sur la marge.</p>"
                "<p><strong>Objectif :</strong> remplacer un patchwork d'outils "
                "génériques (CRM cloud, Drive partagé, mail) par <em>une seule "
                "plateforme métier</em> conçue autour des flux réels de l'entreprise — "
                "demande, devis, intervention, facture — accessible côté admin, "
                "client et technicien terrain.</p>"
            ),
            solution=(
                "<p>Le défi : bâtir un système robuste capable de gérer plusieurs "
                "milliers d'interventions par an, dans des zones où le réseau "
                "mobile est instable, sans complexifier le quotidien des "
                "techniciens habitués au papier.</p>"
                "<ul>"
                "<li><strong>Trois portails distincts</strong> mais cohérents : "
                "admin (pilotage global), client (suivi temps réel), technicien "
                "(planning offline-first).</li>"
                "<li><strong>Module devis / facture</strong> avec génération PDF "
                "conforme à la norme française (Factur-X, EN 16931).</li>"
                "<li><strong>Synchronisation hors-ligne</strong> sur le portail "
                "technicien : interventions saisies en zone blanche, remontées "
                "automatiquement dès retour en réseau.</li>"
                "<li><strong>Authentification renforcée</strong> (2FA OTP + "
                "verrouillage automatique) pour respecter la confidentialité des "
                "contrats industriels.</li>"
                "</ul>"
            ),
            strategy=(
                "<p>Une refonte aussi structurelle exige une démarche progressive. "
                "Plutôt que de tout livrer en une fois — risque classique d'un "
                "rejet utilisateur — nous avons découpé le projet en quatre "
                "phases, chacune validée en conditions réelles avant de passer "
                "à la suivante.</p>"
            ),
            result=(
                "<p>Six mois après la mise en production, TitanTech a divisé par "
                "trois son délai moyen entre la demande client et l'envoi du "
                "devis. Les techniciens saisissent leurs interventions le jour "
                "même, là où il fallait souvent une semaine pour qu'un rapport "
                "remonte au bureau.</p>"
                "<ul>"
                "<li><strong>−63 %</strong> sur le délai devis (4,2 j → 1,5 j en moyenne).</li>"
                "<li><strong>+38 %</strong> de capacité facturable mensuelle, à équipe constante.</li>"
                "<li><strong>0 perte</strong> d'information entre techniciens et bureau "
                "depuis le passage à la plateforme.</li>"
                "<li><strong>NPS client passé de 32 à 71</strong> sur 6 mois.</li>"
                "</ul>"
                "<p>Le code source a été livré avec sa documentation et son "
                "historique Git — TitanTech reste maître de son infrastructure.</p>"
            ),
            technologies=[
                "Django 5",
                "Python 3.13",
                "PostgreSQL 16",
                "HTMX",
                "Alpine.js",
                "Tailwind CSS",
                "Celery",
                "Redis",
                "WeasyPrint (PDF Factur-X)",
                "Stripe Connect",
                "Sentry",
                "Docker",
            ],
            is_featured=True,
            is_published=True,
            audit_results={
                # Note UI/UX manuelle TUS (les autres scores seront remplis par
                # `audit_portfolio_projects` quand PAGESPEED_API_KEY sera renseigné).
                "ui_ux": {
                    "score": 92,
                    "measured_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                },
            },
        )

        project, created = Project.objects.update_or_create(slug=SLUG, defaults=defaults)
        verb = "créé" if created else "mis à jour"
        self.stdout.write(self.style.SUCCESS(
            f"[OK] Projet « {project.title} » {verb} (slug={project.slug})."
        ))

        # ── Phases de stratégie (Ch.03 timeline) ─────────────────────
        phases = [
            {
                "phase_label": "Phase 1 · Cadrage",
                "title": "Audit terrain & cartographie des flux",
                "icon": StrategyPhaseIcon.SEARCH,
                "description": (
                    "Trois jours sur site avec les équipes admin, client et "
                    "technicien pour observer les flux réels — pas les "
                    "process supposés. Restitution sous forme de carte des "
                    "frictions, validée par la direction avant tout code."
                ),
                "order": 1,
            },
            {
                "phase_label": "Phase 2 · Architecture",
                "title": "Modélisation & prototypage des 3 portails",
                "icon": StrategyPhaseIcon.ARCHITECTURE,
                "description": (
                    "Maquettes haute fidélité validées sur chaque portail. "
                    "Choix d'architecture : Django + HTMX pour rester léger, "
                    "PostgreSQL pour la robustesse, Service Worker pour "
                    "l'offline-first technicien."
                ),
                "order": 2,
            },
            {
                "phase_label": "Phase 3 · Développement",
                "title": "Itérations bi-mensuelles avec démo client",
                "icon": StrategyPhaseIcon.CODE,
                "description": (
                    "Sprints de deux semaines, chacun clos par une démo en "
                    "visio avec la direction TitanTech. Tests automatisés "
                    "sur chaque module métier (devis, factures, plannings). "
                    "Couverture finale : 87 %."
                ),
                "order": 3,
            },
            {
                "phase_label": "Phase 4 · Déploiement",
                "title": "Bascule progressive & accompagnement terrain",
                "icon": StrategyPhaseIcon.DEPLOY,
                "description": (
                    "Mise en production par lots : un site pilote pendant "
                    "quatre semaines, puis bascule complète. Formation "
                    "présentielle des techniciens, support 30 jours en "
                    "post-livraison conformément à la garantie TUS."
                ),
                "order": 4,
            },
        ]

        StrategyPhase.objects.filter(project=project).delete()
        for phase_data in phases:
            StrategyPhase.objects.create(project=project, **phase_data)

        self.stdout.write(self.style.SUCCESS(
            f"[OK] {len(phases)} phases de stratégie créées."
        ))

        # ── Invalidation du cache home (compteur portfolio) ──────────
        try:
            from django.core.cache import cache
            cache.delete("homepage_portfolio_count")
        except Exception:  # pragma: no cover
            pass

        self.stdout.write("\nProjet visible sur :")
        self.stdout.write(self.style.MIGRATE_HEADING(
            f"  http://localhost:8000/nos-signatures/{project.slug}/"
        ))
