from __future__ import annotations

import os
import sys
import urllib.request
from typing import Optional

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError

from apps.chroniques.models import Article


COVER_PLACEHOLDER_URL = "https://images.unsplash.com/photo-y1efzWi1XYU?q=80&w=1200&auto=format&fit=crop"
COVER_PLACEHOLDER_URL_CYBER = "https://images.unsplash.com/photo-HbrkV4cRThE?q=80&w=1200&auto=format&fit=crop"


class Command(BaseCommand):
    help = "Publie deux articles Chroniques (design/charte et bonnes pratiques cybersécurité). Optionnel: ajoute des images de couverture."

    def add_arguments(self, parser):
        parser.add_argument(
            "--with-covers",
            action="store_true",
            help="Télécharger et attacher des images de couverture (Unsplash thématiques).",
        )

    def _download_cover(self, url: str) -> Optional[ContentFile]:
        try:
            self.stdout.write(f"Téléchargement cover: {url}")
            with urllib.request.urlopen(url, timeout=15) as resp:
                data = resp.read()
            return ContentFile(data)
        except Exception as e:
            self.stderr.write(f"Échec téléchargement: {e}")
            return None

    def handle(self, *args, **options):
        with_covers: bool = options.get("with_covers", False)

        articles = [
            {
                "slug": "design-charte-graphique-entreprise",
                "title": "Concevoir une charte graphique qui sert l’entreprise",
                "excerpt": (
                    "Pourquoi une charte claire, cohérente et exploitable vaut mieux qu’un logo isolé."
                ),
                "body": (
                    "Une charte graphique efficace n’est pas un document cosmétique. "
                    "Elle condense des choix visuels et d’usage qui facilitent le quotidien: "
                    "typographies lisibles, palette accessible, déclinaisons logo, règles d’espacement, "
                    "composants UI réutilisables.\n\n"
                    "Points clés:\n"
                    "• Clarifier les usages (print, web, social, email).\n"
                    "• Prévoir les contraintes (dark mode, accessibilité, contrastes).\n"
                    "• Documenter les composants (boutons, cartes, formulaires).\n"
                    "• Fournir des assets prêts à l’emploi (SVG, PNG, variantes).\n\n"
                    "Une bonne charte accélère la production et garantit une image cohérente à chaque point de contact."
                ),
                "cover_url": COVER_PLACEHOLDER_URL,
            },
            {
                "slug": "bonnes-pratiques-cybersecurite",
                "title": "Bonnes pratiques en cybersécurité pour les PME",
                "excerpt": (
                    "Mesures simples à forte valeur: MFA, sauvegardes, mises à jour, sensibilisation."
                ),
                "body": (
                    "La sécurité est un processus, pas un produit. "
                    "Quelques pratiques apportent 80% du bénéfice pour un effort raisonnable:\n\n"
                    "1) Activer la double authentification (MFA) pour tous les accès sensibles.\n"
                    "2) Sauvegardes régulières et tests de restauration.\n"
                    "3) Mise à jour systématique des systèmes et dépendances.\n"
                    "4) Sensibilisation des équipes (phishing, mots de passe, partage).\n"
                    "5) Principe du moindre privilège et revue des accès trimestrielle.\n\n"
                    "Couplées à une supervision basique (logs, alertes), ces mesures réduisent fortement le risque."
                ),
                "cover_url": COVER_PLACEHOLDER_URL_CYBER,
            },
        ]

        created_or_updated = []
        for a in articles:
            obj, created = Article.objects.get_or_create(
                slug=a["slug"],
                defaults={
                    "title": a["title"],
                    "excerpt": a["excerpt"],
                    "body": a["body"],
                    "is_published": True,
                },
            )
            if not created:
                # mise à jour du contenu si déjà présent
                obj.title = a["title"]
                obj.excerpt = a["excerpt"]
                obj.body = a["body"]
                obj.is_published = True
                obj.save()

            if with_covers and a.get("cover_url"):
                file = self._download_cover(a["cover_url"])
                if file:
                    filename = f"{a['slug']}.jpg"
                    obj.cover_image.save(filename, file, save=True)
                    self.stdout.write(self.style.SUCCESS(f"✓ Cover attachée: {filename}"))

            created_or_updated.append((obj.slug, created))

        for slug, created in created_or_updated:
            status = "créé" if created else "mis à jour"
            self.stdout.write(self.style.SUCCESS(f"✓ Article {status}: {slug}"))

        self.stdout.write(self.style.SUCCESS("Terminé."))
