"""Insère le projet portfolio « ITEAG » — plateforme académique et institutionnelle.

Usage :
    python manage.py seed_iteag              # créé / met à jour
    python manage.py seed_iteag --si-absent  # ne crée que si la fiche manque
    python manage.py seed_iteag --clear      # supprime le projet
    python manage.py seed_iteag --sans-images  # ne réattache pas les captures

Le projet pointe sur l'environnement de préproduction OVH, seul environnement
en ligne à ce jour. Basculer ``PROJECT_URL`` sur ``https://iteag.org`` le jour
de la bascule du domaine.

Idempotent : la commande s'appuie sur le slug ``iteag``. Relancée, elle met à
jour les contenus sans créer de doublon ; ``--clear`` supprime proprement (et
avec lui les phases de stratégie en cascade).

Les captures vivent dans ``assets/iteag/`` à côté de cette commande — elles
sont réécrites dans le stockage de médias à chaque exécution, afin que la
production (Cloudinary) les reçoive comme le développement (disque local).
"""

from __future__ import annotations

from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand
from django.db import transaction


SLUG = "iteag"
PROJECT_URL = "https://iteag-preprod.137.74.169.188.sslip.io"
ASSETS_DIR = Path(__file__).resolve().parent / "assets" / "iteag"

# Champ image → fichier source dans ASSETS_DIR
IMAGES = {
    "thumbnail": "iteag-thumbnail.webp",
    "image_ch02": "iteag-ch02.webp",
    "image_ch03": "iteag-ch03.webp",
    "image_ch04": "iteag-ch04.webp",
}


class Command(BaseCommand):
    help = "Crée (ou met à jour) le projet portfolio « ITEAG »."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear", action="store_true",
            help="Supprime le projet (et ses phases / images).",
        )
        parser.add_argument(
            "--si-absent", action="store_true",
            help=(
                "Ne fait rien si la fiche existe déjà. Mode du post-déploiement : "
                "le premier déploiement publie l'étude de cas, les suivants "
                "laissent intactes les retouches faites depuis l'admin."
            ),
        )
        parser.add_argument(
            "--sans-images", action="store_true",
            help="Ne réattache pas les captures (contenu textuel seulement).",
        )

    # La fiche, ses captures et ses phases arrivent ensemble ou pas du tout.
    # Sans cela, un envoi de capture qui échoue — le stockage est distant en
    # production — laisse une fiche créée mais vide, que « --si-absent »
    # figerait à chaque déploiement suivant.
    @transaction.atomic
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

        if options["si_absent"]:
            existante = Project.objects.filter(slug=SLUG).first()
            # Une fiche sans phase n'est pas une fiche : c'est le résidu d'un
            # passage interrompu. La sauter la figerait dans cet état. On ne
            # s'abstient que devant une étude de cas effectivement montée.
            if existante is not None and StrategyPhase.objects.filter(project=existante).exists():
                self.stdout.write(
                    f"[--] Fiche « {SLUG} » déjà présente : rien à faire (--si-absent)."
                )
                return
            if existante is not None:
                self.stdout.write(self.style.WARNING(
                    f"[!!] Fiche « {SLUG} » présente mais sans phase — passage "
                    "précédent interrompu. Réécriture."
                ))

        # ── Identité projet ──────────────────────────────────────────
        defaults = dict(
            title="ITEAG",
            project_type=ProjectType.OUTILS,
            client_name="Institut de Théologie Évangélique des Antilles et de la Guyane",
            url=PROJECT_URL,
            objective=(
                "<p>L'ITEAG forme depuis des décennies des responsables d'Église "
                "en Guadeloupe, en Martinique et en Guyane. Association loi 1905, "
                "l'institut fait tenir un cursus de six ans sur quatre semaines "
                "de session par an — Carnaval, Pâques, grandes vacances, "
                "Toussaint — pour des étudiants répartis sur trois territoires "
                "et deux mille kilomètres d'océan.</p>"
                "<p>Le site existant était une vitrine WordPress. Il présentait "
                "l'institut, mais tout ce qui fait sa vie passait ailleurs : les "
                "candidatures par téléphone, les vidéos de cours distribuées "
                "<em>sur demande au secrétariat</em>, plus de trois mille ouvrages "
                "de bibliothèque catalogués hors ligne, le suivi des crédits ECTS "
                "tenu dans des tableurs.</p>"
                "<p><strong>La commande :</strong> sortir de la vitrine sans "
                "sacrifier ce qui fonctionne. Une plateforme unique où le visiteur "
                "trouve sa formation et candidate en ligne, où l'étudiant suit ses "
                "crédits et ses cours, où l'enseignant corrige, où le secrétariat "
                "pilote — et dont l'ITEAG reste propriétaire, code compris.</p>"
            ),
            solution=(
                "<p>La difficulté n'était pas de construire un espace de cours de "
                "plus. Elle était de modéliser un système pédagogique qui ne "
                "ressemble à aucun autre : sessions intensives plutôt que "
                "semestres, deux filières — diplôme ITEAG et Bachelor délivré "
                "avec la FLTE de Vaux-sur-Seine — qui suivent les mêmes cours "
                "magistraux mais pas les mêmes règles de validation, des crédits "
                "obtenus dans une institution partenaire à réintégrer dans la "
                "progression, des stages convertibles en dissertation.</p>"
                "<ul>"
                "<li><strong>Quatre portails sur un seul socle</strong> — public, "
                "étudiant, enseignant, administration — pour éviter quatre "
                "applications à maintenir et quatre vérités sur les mêmes données.</li>"
                "<li><strong>Diffusion vidéo à droit revérifié.</strong> Les cours "
                "filmés sont la valeur de l'institut : aucune adresse de fichier "
                "n'apparaît dans la page, le droit est recontrôlé à chaque demande "
                "de lecture, chaque octroi est journalisé et le nombre de flux "
                "simultanés par compte est plafonné. Une révocation prend effet "
                "immédiatement.</li>"
                "<li><strong>Une seule autorité d'accès.</strong> Rôle et droit "
                "sont deux questions distinctes : le rôle dit qui vous êtes, le "
                "droit dit ce que vous pouvez suivre. La décision se calcule dans "
                "un point unique du code, dans un ordre fixe — et le secrétariat "
                "octroie, suspend ou prolonge sans développeur.</li>"
                "<li><strong>Un débit incertain comme contrainte de conception.</strong> "
                "Depuis la Guyane et la Martinique, la bande passante n'est pas "
                "acquise : la lecture s'adapte au réseau réel plutôt que de "
                "supposer la fibre.</li>"
                "<li><strong>Aucun framework JavaScript.</strong> HTMX pour les "
                "échanges serveur, composants natifs pour le reste, et une "
                "politique de sécurité de contenu stricte — sans "
                "<code>unsafe-inline</code> ni <code>unsafe-eval</code>. Toute "
                "bibliothèque qui évalue des chaînes est écartée par principe.</li>"
                "</ul>"
            ),
            strategy=(
                "<p>Une refonte qui touche à la fois au site public, à la "
                "scolarité et à la pédagogie ne se livre pas d'un bloc : elle se "
                "vérifie par étapes, chacune close par une décision écrite.</p>"
                "<p>Le dépôt en porte la trace — un cahier des charges "
                "exécutable, des décisions d'architecture datées et révisables, "
                "un manuel d'exploitation, un registre des traitements. Ce que "
                "l'ITEAG reçoit n'est pas seulement une plateforme : c'est le "
                "dossier qui permet de la reprendre.</p>"
            ),
            result=(
                "<p>La plateforme est en préproduction sur OVH Cloud, complète et "
                "parcourable de bout en bout. Le site public est éditable par le "
                "secrétariat sans passer par un développeur ; le catalogue de la "
                "bibliothèque est en ligne ; la candidature se dépose depuis un "
                "téléphone.</p>"
                "<ul>"
                "<li><strong>13 applications métier</strong> aux dépendances "
                "déclarées — le graphe est vérifié à chaque exécution de la suite, "
                "une dépendance non déclarée fait échouer les tests.</li>"
                "<li><strong>1 459 fonctions de test sur 127 modules</strong>, "
                "soit 3 092 cas exécutés, sur PostgreSQL comme en intégration "
                "continue. <strong>93 % de couverture</strong> — et 100 % sur "
                "le point de contrôle d'accès, celui dont dépend la valeur des "
                "cours filmés.</li>"
                "<li><strong>≈ 55 000 lignes de Python</strong> et plus de 200 "
                "gabarits, sans dépendance à un plugin propriétaire.</li>"
                "<li><strong>Un jeu de démonstration idempotent</strong> qui peuple "
                "toute la plateforme : chaque écran y montre au moins un cas de "
                "chaque état qu'il sait afficher — une liste dont toutes les "
                "lignes se ressemblent ne démontre ni ses filtres ni ses actions.</li>"
                "</ul>"
                "<p>Reste la bascule du domaine et la reprise des contenus "
                "historiques, qui appartiennent au calendrier de l'institut. Le "
                "code, sa documentation et son historique Git lui sont acquis.</p>"
            ),
            technologies=[
                "Django 5.2",
                "Wagtail 7",
                "Python 3.12",
                "PostgreSQL 16",
                "Redis",
                "Celery",
                "HTMX",
                "Tailwind CSS 4",
                "WeasyPrint",
                "django-otp (2FA)",
                "django-axes",
                "django-csp",
                "Cloudflare R2 / Turnstile",
                "HLS.js",
                "Sentry",
                "Docker / Coolify",
                "OVH Cloud",
            ],
            is_featured=True,
            is_published=True,
        )

        project, created = Project.objects.update_or_create(slug=SLUG, defaults=defaults)
        verb = "créé" if created else "mis à jour"
        self.stdout.write(self.style.SUCCESS(
            f"[OK] Projet « {project.title} » {verb} (slug={project.slug})."
        ))

        # ── Captures (miniature + Ch.02 / Ch.03 / Ch.04) ─────────────
        if options["sans_images"]:
            self.stdout.write("[--] Captures ignorées (--sans-images).")
        else:
            self._attacher_images(project)

        # ── Phases de stratégie (Ch.03 timeline) ─────────────────────
        phases = [
            {
                "phase_label": "Phase 1 · Cadrage",
                "title": "Relever le modèle pédagogique réel",
                "icon": StrategyPhaseIcon.MEETING,
                "description": (
                    "Sessions intensives, crédits ECTS, double filière ITEAG / "
                    "Bachelor FLTE, stages convertibles en dissertation : le "
                    "fonctionnement de l'institut a été écrit avant la première "
                    "ligne de code, dans un cahier des charges revu et corrigé "
                    "par un audit avant signature."
                ),
                "order": 1,
            },
            {
                "phase_label": "Phase 2 · Architecture",
                "title": "Un monolithe modulaire, pas quatre applications",
                "icon": StrategyPhaseIcon.ARCHITECTURE,
                "description": (
                    "Treize applications Django découplées, un seul déploiement. "
                    "Les dépendances entre applications sont déclarées et "
                    "vérifiées par la suite de tests : le graphe reste acyclique "
                    "et les entorses connues ne peuvent que diminuer."
                ),
                "order": 2,
            },
            {
                "phase_label": "Phase 3 · Développement",
                "title": "Rendu serveur, interface sobre, tests d'abord",
                "icon": StrategyPhaseIcon.CODE,
                "description": (
                    "Django et Wagtail pour l'éditorial, HTMX pour les échanges, "
                    "aucun framework JavaScript. Le système de design vit dans "
                    "une source unique afin que l'interface reste conforme à la "
                    "charte ITEAG écran après écran."
                ),
                "order": 3,
            },
            {
                "phase_label": "Phase 4 · Sécurité & conformité",
                "title": "Protéger le contenu et les personnes",
                "icon": StrategyPhaseIcon.SECURITY,
                "description": (
                    "Double authentification pour le personnel, verrouillage "
                    "après tentatives échouées, politique de sécurité de contenu "
                    "stricte, journal des accès vidéo. Côté données : registre "
                    "des traitements et politique de gestion, rédigés avec la "
                    "plateforme, pas après."
                ),
                "order": 4,
            },
            {
                "phase_label": "Phase 5 · Exploitation",
                "title": "Livrer, et rendre l'exploitation reprenable",
                "icon": StrategyPhaseIcon.DEPLOY,
                "description": (
                    "Préproduction sur OVH Cloud administrée par Coolify, "
                    "déploiement décrit par un fichier Compose lisible sans "
                    "l'interface qui l'exécute. Sauvegardes, supervision et "
                    "conduite d'incident sont documentées dans un manuel "
                    "d'exploitation remis à l'institut."
                ),
                "order": 5,
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

    # ──────────────────────────────────────────────────────────────────
    def _attacher_images(self, project) -> None:
        """Réécrit les captures dans le stockage de médias configuré."""
        attachees = 0
        for champ, nom_fichier in IMAGES.items():
            source = ASSETS_DIR / nom_fichier
            if not source.exists():
                self.stdout.write(self.style.WARNING(
                    f"[!!] Capture absente, champ {champ} laissé vide : {source}"
                ))
                continue
            fichier = getattr(project, champ)
            # Sans suppression préalable, le stockage suffixe le nom à chaque
            # exécution (iteag-ch02_a1b2c3.webp) et accumule les doublons.
            if fichier:
                fichier.delete(save=False)
            with source.open("rb") as f:
                fichier.save(nom_fichier, File(f), save=False)
            attachees += 1
        if attachees:
            project.save()
            self.stdout.write(self.style.SUCCESS(
                f"[OK] {attachees} capture(s) attachée(s)."
            ))
