"""Injecte des témoignages d'exemple pour visualiser la section home.

Usage :
    python manage.py seed_testimonials          # ajoute les exemples (idempotent)
    python manage.py seed_testimonials --clear   # supprime UNIQUEMENT les exemples

Les témoignages d'exemple sont marqués par un préfixe interne reconnaissable
dans le champ `content`, pour pouvoir les retirer sans toucher aux vrais avis.
"""

from __future__ import annotations

from django.core.cache import cache
from django.core.management.base import BaseCommand


# Marqueur invisible (zero-width) ajouté en fin de contenu pour identifier
# les exemples générés par cette commande sans polluer l'affichage.
_DEMO_MARKER = "\u200b"  # zero-width space


DEMO_TESTIMONIALS = [
    {
        "client_name": "Marie-Laure Constant",
        "company_name": "Nettoyage Express SARL",
        "position": "Gérante",
        "content": (
            "Avant, nos interventions se perdaient entre les fichiers Excel et les SMS. "
            "Trait d'Union a construit une plateforme où tout est centralisé : planning, "
            "devis, factures. On n'oublie plus rien, et nos clients voient l'avancement en temps réel."
        ),
        "rating": 5,
        "order": 1,
    },
    {
        "client_name": "Joseph Eliacin",
        "company_name": "EEBC",
        "position": "Responsable administratif",
        "content": (
            "Un seul outil pour piloter membres, activités et finances. L'accompagnement a été "
            "clair du début à la fin, sans jargon. On a gardé la main sur notre contenu — c'est "
            "exactement ce qu'on cherchait."
        ),
        "rating": 5,
        "order": 2,
    },
    {
        "client_name": "Sandra Mathurin",
        "company_name": "Atelier Créole",
        "position": "Fondatrice",
        "content": (
            "Une boutique en ligne rapide, élégante et qui convertit vraiment. Le suivi des "
            "commandes est devenu un jeu d'enfant. Je recommande sans hésiter pour les entrepreneurs d'Outre-mer."
        ),
        "rating": 5,
        "order": 3,
    },
]


class Command(BaseCommand):
    help = "Injecte (ou supprime) des témoignages d'exemple pour la home."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear", action="store_true",
            help="Supprime uniquement les témoignages d'exemple générés par cette commande.",
        )

    def handle(self, *args, **options):
        from apps.pages.models import Testimonial

        if options["clear"]:
            qs = Testimonial.objects.filter(content__endswith=_DEMO_MARKER)
            count = qs.count()
            qs.delete()
            cache.delete("homepage_testimonials")
            self.stdout.write(self.style.SUCCESS(
                f"[OK] {count} témoignage(s) d'exemple supprimé(s)."
            ))
            return

        created = 0
        for data in DEMO_TESTIMONIALS:
            content = data["content"] + _DEMO_MARKER
            obj, was_created = Testimonial.objects.get_or_create(
                client_name=data["client_name"],
                company_name=data["company_name"],
                defaults={
                    "position": data["position"],
                    "content": content,
                    "rating": data["rating"],
                    "order": data["order"],
                    "is_published": True,
                },
            )
            if was_created:
                created += 1
                self.stdout.write(f"  + {obj.client_name} ({obj.company_name})")
            else:
                self.stdout.write(f"  = déjà présent : {obj.client_name}")

        cache.delete("homepage_testimonials")
        self.stdout.write(self.style.SUCCESS(
            f"\n[OK] {created} témoignage(s) d'exemple ajouté(s). "
            f"Visibles sur la page d'accueil.\n"
            f"Pour les retirer : python manage.py seed_testimonials --clear"
        ))
