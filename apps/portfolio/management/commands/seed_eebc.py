"""Insère le projet portfolio « EEBC » — plateforme de gestion d'église.

Usage :
    python manage.py seed_eebc                      # créé / met à jour
    python manage.py seed_eebc --slug <autre-slug>  # met à jour une fiche existante
    python manage.py seed_eebc --si-absent          # ne crée que si la fiche manque
    python manage.py seed_eebc --clear              # supprime le projet

Contenu relevé dans le dépôt beaudelaire1/gestion-eebc : 19 applications
métier, 67 342 lignes de Python hors migrations, 362 gabarits, 645 fonctions
de test sur 35 modules.

Idempotent : la commande s'appuie par défaut sur le slug ``eebc``. Relancée,
elle met à jour les contenus sans créer de doublon ; ``--clear`` supprime
proprement (et avec lui les phases de stratégie en cascade).

Une fiche EEBC créée à la main dans l'admin ne porte pas forcément ce slug.
Dans ce cas, ``--slug`` vise la fiche d'origine : la commande la met à jour
au lieu d'en publier une seconde. Le slug se lit dans l'adresse de la page,
``/nos-signatures/<slug>/``.

Les captures téléversées depuis l'admin sont conservées : les champs d'image
ne figurent pas dans ``defaults``, donc ``update_or_create`` n'y touche pas.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

SLUG = "eebc"
PROJECT_URL = "https://eglise-ebc.org"


class Command(BaseCommand):
    help = "Crée (ou met à jour) le projet portfolio « EEBC »."

    def add_arguments(self, parser):
        parser.add_argument(
            "--slug", default=SLUG,
            help=(
                "Slug de la fiche à écrire. Par défaut « %(default)s ». "
                "Si l'étude de cas a été créée à la main sous un autre slug, "
                "le passer ici : la commande met alors à jour la fiche "
                "d'origine au lieu d'en créer une seconde."
            ),
        )
        parser.add_argument(
            "--clear", action="store_true",
            help="Supprime le projet (et ses phases).",
        )
        parser.add_argument(
            "--si-absent", action="store_true",
            help=(
                "Ne fait rien si la fiche existe déjà. Mode du post-déploiement : "
                "le premier déploiement publie l'étude de cas, les suivants "
                "laissent intactes les retouches faites depuis l'admin."
            ),
        )

    # La fiche et ses phases arrivent ensemble ou pas du tout : une panne en
    # cours de route ne doit pas laisser une étude de cas à moitié publiée.
    @transaction.atomic
    def handle(self, *args, **options):
        from apps.portfolio.models import (
            Project,
            ProjectType,
            StrategyPhase,
            StrategyPhaseIcon,
        )

        slug = options["slug"]

        if options["clear"]:
            qs = Project.objects.filter(slug=slug)
            count = qs.count()
            qs.delete()
            self.stdout.write(self.style.SUCCESS(
                f"[OK] {count} projet(s) supprimé(s) (slug={slug!r})."
            ))
            return

        if options["si_absent"]:
            existante = Project.objects.filter(slug=slug).first()
            # Une fiche sans phase est le résidu d'un passage interrompu, pas
            # une étude de cas : la sauter la figerait dans cet état.
            if existante is not None and StrategyPhase.objects.filter(project=existante).exists():
                self.stdout.write(
                    f"[--] Fiche « {slug} » déjà présente : rien à faire (--si-absent)."
                )
                return
            if existante is not None:
                self.stdout.write(self.style.WARNING(
                    f"[!!] Fiche « {slug} » présente mais sans phase — passage "
                    "précédent interrompu. Réécriture."
                ))

        defaults = dict(
            title="EEBC",
            project_type=ProjectType.OUTILS,
            client_name="Église Évangélique Baptiste de Cayenne",
            url=PROJECT_URL,
            objective=(
                "<p>L'Église Évangélique Baptiste de Cayenne réunit plusieurs "
                "centaines de personnes chaque dimanche. Comme toute "
                "association cultuelle française, elle porte des obligations "
                "que peu de gens associent au mot « église » : tracer chaque "
                "don, émettre des reçus fiscaux numérotés, tenir des budgets "
                "par département, garder mémoire de qui a été visité, "
                "baptisé, marié.</p>"
                "<p>Tout cela tenait dans des tableurs, des carnets et la "
                "mémoire des responsables. Les dons se notaient à la main, "
                "les reçus fiscaux se retapaient un par un en fin d'année, "
                "les groupes se coordonnaient par messages, et la personne "
                "qui savait où en était une visite était celle qui l'avait "
                "faite.</p>"
                "<p><strong>La commande :</strong> une plateforme unique, "
                "tenue par les membres de l'église eux-mêmes et non par des "
                "informaticiens, qui absorbe la comptabilité, les membres, "
                "les groupes, le culte et la communication — sans transformer "
                "la vie de l'église en saisie de formulaires.</p>"
            ),
            solution=(
                "<p>La difficulté n'était pas technique au départ, elle était "
                "de modélisation. Une église ne se range pas dans un "
                "organigramme d'entreprise : la même personne est diacre, "
                "responsable d'un groupe de maison et chauffeur le dimanche "
                "matin. Un logiciel qui impose un rôle unique par compte "
                "oblige à mentir sur la réalité dès le premier jour.</p>"
                "<ul>"
                "<li><strong>Douze rôles cumulables.</strong> Administrateur, "
                "pasteur, ancien, diacre, responsable de club biblique, "
                "moniteur, chauffeur, responsable de groupe, secrétariat, "
                "finance, encadrant, membre : un compte en porte autant que "
                "la personne en assume, et les écrans s'ouvrent en "
                "conséquence.</li>"
                "<li><strong>Le reçu fiscal est un document réglementé, pas "
                "un PDF.</strong> Numéroté, unique, rattaché aux transactions "
                "qu'il couvre, il suit un cycle brouillon → émis → envoyé → "
                "annulé. On n'efface pas un reçu émis : on l'annule, et la "
                "trace reste. C'est la condition pour que le donateur puisse "
                "le présenter à l'administration fiscale.</li>"
                "<li><strong>Du paiement au reçu, sans ressaisie.</strong> Un "
                "don en ligne passe par Stripe, crée sa transaction, "
                "déclenche son reçu et part par courriel — le trésorier "
                "n'intervient que s'il y a une anomalie.</li>"
                "<li><strong>Joindre les gens là où ils sont.</strong> En "
                "Guyane, l'information circule sur WhatsApp bien avant le "
                "courriel. La plateforme parle donc WhatsApp Cloud API, SMS "
                "et courriel depuis le même écran d'envoi.</li>"
                "<li><strong>Dix-neuf applications pour une seule "
                "institution :</strong> membres et familles, visites, "
                "groupes de maison, club biblique des enfants, jeunesse, "
                "culte et planning, transport, inventaire, départements, "
                "budgets, campagnes de collecte, import de données.</li>"
                "<li><strong>Une application mobile Flutter</strong> pour "
                "iOS et Android, adossée à la même API REST que le site — un "
                "seul modèle de données, pas deux vérités.</li>"
                "</ul>"
            ),
            strategy=(
                "<p>Une église ne s'arrête pas le temps d'une refonte. Le "
                "projet a donc été livré par blocs utilisables, en "
                "commençant par celui dont l'erreur coûte le plus cher — "
                "l'argent — et en terminant par ceux qui demandaient "
                "l'adhésion du plus grand nombre.</p>"
                "<p>Chaque bloc est parti d'une observation sur place plutôt "
                "que d'un cahier des charges : ce qu'un responsable fait "
                "réellement un dimanche matin ne ressemble jamais tout à "
                "fait à ce qu'il en décrit en réunion.</p>"
            ),
            result=(
                "<p>La plateforme est en service à Cayenne. Les dons en ligne "
                "produisent leurs reçus sans intervention, les responsables "
                "de groupe tiennent leurs listes eux-mêmes, et le trésorier "
                "édite en fin d'année ce qu'il retapait auparavant reçu par "
                "reçu.</p>"
                "<ul>"
                "<li><strong>19 applications métier</strong>, "
                "<strong>67 342 lignes de Python</strong> hors migrations et "
                "<strong>362 gabarits</strong>.</li>"
                "<li><strong>645 fonctions de test sur 35 modules</strong>, "
                "avec une attention particulière au chemin du don : c'est "
                "celui où une erreur se voit sur un document fiscal.</li>"
                "<li><strong>Reçus fiscaux conformes</strong> à la "
                "réglementation française des associations cultuelles, "
                "numérotés et traçables, annulables mais jamais "
                "effaçables.</li>"
                "<li><strong>Une application mobile iOS et Android</strong> "
                "sur la même API que le site.</li>"
                "<li><strong>Un site public</strong> avec sa page de don, "
                "administrable par le secrétariat depuis le même outil.</li>"
                "</ul>"
                "<p>L'église est propriétaire de son code et de ses données. "
                "Le jour où elle voudra changer de prestataire, elle "
                "emportera les deux.</p>"
            ),
            technologies=[
                "Django 4.2",
                "Python 3.11",
                "PostgreSQL",
                "Django REST Framework",
                "JWT",
                "HTMX",
                "Alpine.js",
                "Bootstrap 5",
                "Celery",
                "Redis",
                "WeasyPrint",
                "Stripe",
                "WhatsApp Cloud API",
                "Flutter (iOS & Android)",
                "Render",
            ],
            is_featured=True,
            is_published=True,
        )

        project, created = Project.objects.update_or_create(slug=slug, defaults=defaults)
        self.stdout.write(self.style.SUCCESS(
            f"[OK] Projet « {project.title} » {'créé' if created else 'mis à jour'} "
            f"(slug={project.slug})."
        ))

        phases = [
            {
                "phase_label": "Phase 1 · Cadrage",
                "title": "Observer un dimanche avant d'écrire une ligne",
                "icon": StrategyPhaseIcon.MEETING,
                "description": (
                    "Relever ce qui se passe réellement : qui note les dons, "
                    "où atterrit l'information d'une visite, comment se "
                    "décide une dépense de département. Le cumul des rôles "
                    "est sorti de là, et il a structuré tout le reste."
                ),
                "order": 1,
            },
            {
                "phase_label": "Phase 2 · Finance",
                "title": "Le noyau où l'erreur coûte le plus cher",
                "icon": StrategyPhaseIcon.SECURITY,
                "description": (
                    "Transactions, dons en ligne, reçus fiscaux et budgets "
                    "d'abord. Un reçu fiscal engage l'église devant "
                    "l'administration : sa numérotation, son cycle de vie et "
                    "son impossibilité d'être effacé ont été traités avant "
                    "toute fonctionnalité de confort."
                ),
                "order": 2,
            },
            {
                "phase_label": "Phase 3 · Vie de l'église",
                "title": "Membres, groupes, club biblique, culte",
                "icon": StrategyPhaseIcon.ARCHITECTURE,
                "description": (
                    "Les familles, les événements de vie, les visites, les "
                    "groupes de maison, le club biblique des enfants, le "
                    "planning des cultes et le transport. Chaque responsable "
                    "tient désormais sa propre liste, au lieu de la "
                    "transmettre au secrétariat."
                ),
                "order": 3,
            },
            {
                "phase_label": "Phase 4 · Communication",
                "title": "Parler WhatsApp, parce que c'est là que ça se passe",
                "icon": StrategyPhaseIcon.CODE,
                "description": (
                    "Courriel, SMS et WhatsApp Cloud API depuis un même "
                    "écran, avec journal des envois. L'application mobile "
                    "Flutter est arrivée ici : elle consomme la même API que "
                    "le site, donc elle ne peut pas diverger."
                ),
                "order": 4,
            },
            {
                "phase_label": "Phase 5 · Mise en service",
                "title": "Reprise des données et prise en main par l'équipe",
                "icon": StrategyPhaseIcon.DEPLOY,
                "description": (
                    "Import des membres et de l'historique financier, "
                    "déploiement sur Render avec sauvegardes, puis prise en "
                    "main par les responsables. Le critère de sortie n'était "
                    "pas « le site est en ligne » mais « le secrétariat a "
                    "fait une semaine complète sans nous »."
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
        self.stdout.write("\nProjet visible sur :")
        self.stdout.write(self.style.MIGRATE_HEADING(
            f"  http://localhost:8000/nos-signatures/{project.slug}/"
        ))
