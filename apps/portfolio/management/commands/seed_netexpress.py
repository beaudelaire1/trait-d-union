"""Réécrit le projet portfolio « NetExpress » — plateforme de gestion de chantiers.

Usage :
    python manage.py seed_netexpress              # créé / met à jour
    python manage.py seed_netexpress --si-absent  # ne crée que si la fiche manque
    python manage.py seed_netexpress --clear      # supprime le projet

Contenu relevé sur la branche de production ``for_prod`` du dépôt
beaudelaire1/netexpress : cinq rôles, quatre espaces applicatifs, 41 650
lignes de Python hors migrations, 156 gabarits, 526 fonctions de test sur
51 modules.

Idempotent : la commande s'appuie sur le slug ``netexpress``, celui de la
fiche déjà publiée — elle la réécrit plutôt que d'en créer une seconde.

Les captures déjà téléversées sont conservées : les champs d'image ne
figurent pas dans ``defaults``, donc ``update_or_create`` n'y touche pas.
Seuls le texte, les technologies et les phases sont réécrits.

.. warning::

   Le post-déploiement appelle ``--si-absent``, qui ne fait rien devant une
   fiche déjà présente et pourvue de ses phases. La réécriture d'une fiche
   existante est donc une opération **ponctuelle et volontaire** : lancer
   ``python manage.py seed_netexpress`` une fois sur l'environnement, sans
   l'option. Sans ce passage, la fiche en ligne reste celle d'avant.
"""

from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

SLUG = "netexpress"
PROJECT_URL = "https://www.nettoyageexpresse.fr"


class Command(BaseCommand):
    help = "Crée (ou met à jour) le projet portfolio « NetExpress »."

    def add_arguments(self, parser):
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

    # La fiche et ses phases arrivent ensemble ou pas du tout.
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

        defaults = dict(
            title="NetExpress",
            project_type=ProjectType.OUTILS,
            client_name="NetExpress — espaces verts, nettoyage, peinture, bricolage",
            url=PROJECT_URL,
            objective=(
                "<p>NetExpress intervient chez des particuliers et des "
                "entreprises sur quatre métiers : espaces verts, nettoyage, "
                "peinture, bricolage. Des chantiers courts, nombreux, "
                "dispersés — et une administration qui tenait dans une suite "
                "bureautique.</p>"
                "<p>Les devis se retapaient à chaque demande, les factures se "
                "numérotaient à la main, le planning des chantiers vivait sur "
                "un tableau, et les pièces réclamées par le cabinet comptable "
                "partaient par courriel, en pièces jointes, au fil des "
                "relances. Chaque information existait plusieurs fois, sous "
                "plusieurs versions, et personne ne savait laquelle faisait "
                "foi.</p>"
                "<p><strong>La commande :</strong> une plateforme qui tienne "
                "la chaîne complète — demande, devis, chantier, facture, "
                "pièces comptables — avec une interface qu'un public non "
                "technique puisse utiliser sans formation, et sans jamais "
                "perdre le fil entre le bureau, le terrain, le client et son "
                "comptable.</p>"
            ),
            solution=(
                "<p>Le piège d'un outil de gestion, c'est de devenir un "
                "logiciel de saisie que personne n'ouvre. La contrainte "
                "était donc double : couvrir une chaîne administrative "
                "exigeante, et rester utilisable par un ouvrier sur un "
                "chantier comme par un client qui n'y reviendra qu'une fois "
                "l'an.</p>"
                "<ul>"
                "<li><strong>Cinq rôles, quatre espaces.</strong> Comptable, "
                "client, ouvrier, administrateur business et administrateur "
                "technique. Chacun entre par sa porte — "
                "<code>/client/</code>, <code>/worker/</code>, "
                "<code>/comptabilite/</code>, le tableau de bord "
                "d'administration — et ne voit que ce que son rôle "
                "justifie.</li>"
                "<li><strong>Un numéro de facture ne se réutilise ni ne se "
                "saute.</strong> La numérotation s'alloue sous verrou de "
                "base de données, dans la même transaction que "
                "l'enregistrement, et tient compte des documents supprimés. "
                "C'est une exigence comptable avant d'être un détail "
                "technique : une série trouée est une série à justifier.</li>"
                "<li><strong>Un devis ne s'accepte pas par mégarde.</strong> "
                "La validation se fait en deux temps — un lien, puis un code "
                "à durée limitée — pour qu'un clic distrait n'engage "
                "personne.</li>"
                "<li><strong>Les documents comptables ne s'effacent pas.</strong> "
                "Une suppression les retire des écrans sans les retirer de "
                "l'histoire, et la numérotation continue de les compter.</li>"
                "<li><strong>Le cabinet comptable a son espace, pas une "
                "boîte mail.</strong> Factures clients et fournisseurs, "
                "pièces, échanges et états de lecture vivent dans un fil "
                "dédié : la demande du comptable et la réponse de "
                "l'entreprise restent attachées au document dont elles "
                "parlent.</li>"
                "<li><strong>Une messagerie par espace</strong>, de sorte "
                "qu'un échange avec un client, un ouvrier ou le comptable "
                "reste dans son contexte au lieu de se mélanger dans une "
                "seule boîte.</li>"
                "</ul>"
            ),
            strategy=(
                "<p>L'entreprise ne pouvait pas suspendre son activité "
                "pendant la bascule. Le projet a donc suivi la chaîne "
                "métier dans son ordre naturel — d'abord ce qui entre, puis "
                "ce qui s'exécute, enfin ce qui se justifie — chaque étape "
                "étant mise en service avant que la suivante ne "
                "commence.</p>"
                "<p>L'ordre n'est pas neutre : il fait que le premier "
                "bénéfice visible pour l'entreprise arrive dès la première "
                "livraison, et non à la fin.</p>"
            ),
            result=(
                "<p>Une seule plateforme remplace les fichiers éparpillés. "
                "La demande entre par le site, devient un devis, le devis "
                "devient un chantier, le chantier devient une facture, et la "
                "facture arrive chez le comptable avec ses pièces — sans "
                "qu'aucune de ces étapes ne demande de ressaisie.</p>"
                "<ul>"
                "<li><strong>Quatre espaces</strong> sur un socle unique : "
                "client, ouvrier, comptabilité, administration.</li>"
                "<li><strong>41 650 lignes de Python</strong> hors "
                "migrations et <strong>156 gabarits</strong>.</li>"
                "<li><strong>526 fonctions de test sur 51 modules</strong>, "
                "dont la numérotation des documents et le cycle de "
                "validation des devis — les deux endroits où une erreur "
                "laisse une trace comptable.</li>"
                "<li><strong>Génération PDF</strong> des devis et factures, "
                "avec séries numérotées par année.</li>"
                "<li><strong>Continuité jusqu'au partenaire comptable :</strong> "
                "les pièces utiles lui sont mises à disposition dans son "
                "espace, sans chaîne de courriels parallèle.</li>"
                "</ul>"
                "<p>Le code, sa documentation et son historique appartiennent "
                "à NetExpress.</p>"
            ),
            technologies=[
                "Django",
                "Python",
                "PostgreSQL",
                "Architecture hexagonale (domaine, ports, adaptateurs)",
                "WeasyPrint",
                "Celery",
                "HTMX",
                "Bootstrap",
                "TinyMCE",
                "Render",
            ],
            is_featured=True,
            is_published=True,
        )

        project, created = Project.objects.update_or_create(slug=SLUG, defaults=defaults)
        self.stdout.write(self.style.SUCCESS(
            f"[OK] Projet « {project.title} » {'créé' if created else 'mis à jour'} "
            f"(slug={project.slug})."
        ))

        phases = [
            {
                "phase_label": "Phase 1 · Cadrage",
                "title": "Suivre une demande de bout en bout",
                "icon": StrategyPhaseIcon.SEARCH,
                "description": (
                    "Partir d'une demande réelle et la suivre jusqu'au "
                    "paiement, en notant chaque endroit où l'information est "
                    "retapée. La carte des ressaisies a servi de cahier des "
                    "charges : chacune devait disparaître."
                ),
                "order": 1,
            },
            {
                "phase_label": "Phase 2 · Entrée",
                "title": "Le site public et la demande de devis",
                "icon": StrategyPhaseIcon.DESIGN,
                "description": (
                    "Catalogue des services par métier, fiches détaillées, "
                    "formulaire de devis pré-rempli depuis le service "
                    "consulté. Première mise en service : l'entreprise "
                    "reçoit des demandes qualifiées au lieu d'appels à "
                    "requalifier."
                ),
                "order": 2,
            },
            {
                "phase_label": "Phase 3 · Chaîne documentaire",
                "title": "Devis, factures et numérotation sous verrou",
                "icon": StrategyPhaseIcon.DATABASE,
                "description": (
                    "Le cœur exigeant : séries numérotées par année, "
                    "allocation sous verrou de base, suppression douce, "
                    "génération PDF, et validation de devis en deux temps. "
                    "C'est la partie qui engage l'entreprise, donc celle qui "
                    "porte le plus de tests."
                ),
                "order": 3,
            },
            {
                "phase_label": "Phase 4 · Terrain et clients",
                "title": "Espace ouvrier, espace client, messagerie",
                "icon": StrategyPhaseIcon.CODE,
                "description": (
                    "Planification des chantiers, accès ouvrier à ses tâches, "
                    "suivi client sur ses devis et factures, et une "
                    "messagerie par espace pour que chaque échange reste "
                    "attaché à son contexte."
                ),
                "order": 4,
            },
            {
                "phase_label": "Phase 5 · Comptabilité",
                "title": "Prolonger la plateforme jusqu'au cabinet",
                "icon": StrategyPhaseIcon.DEPLOY,
                "description": (
                    "Le quatrième espace, ajouté après coup parce que le "
                    "besoin est apparu à l'usage : factures fournisseurs, "
                    "pièces, revues et fil d'échange avec le cabinet "
                    "comptable, avec états de lecture. La chaîne "
                    "d'e-mails parallèle s'est arrêtée là."
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
