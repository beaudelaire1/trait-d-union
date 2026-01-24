from __future__ import annotations

from django.core.management.base import BaseCommand

from apps.chroniques.models import Article


class Command(BaseCommand):
    help = "Publie deux articles Chroniques (design/charte et bonnes pratiques cybersecurite)."

    def handle(self, *args, **options):
        articles = [
            {
                "slug": "design-charte-graphique-entreprise",
                "title": "Concevoir une charte graphique qui sert l'entreprise",
                "excerpt": "Pourquoi une charte claire, coherente et exploitable vaut mieux qu'un logo isole.",
                "body": "Une charte graphique efficace n'est pas un document cosmetique. Elle condense des choix visuels et d'usage qui facilitent le quotidien: typographies lisibles, palette accessible, declinaisons logo, regles d'espacement, composants UI reutilisables.\n\nPoints cles:\n- Clarifier les usages (print, web, social, email).\n- Prevoir les contraintes (dark mode, accessibilite, contrastes).\n- Documenter les composants (boutons, cartes, formulaires).\n- Fournir des assets prets a l'emploi (SVG, PNG, variantes).\n\nUne bonne charte accelere la production et garantit une image coherente a chaque point de contact.",
            },
            {
                "slug": "bonnes-pratiques-cybersecurite",
                "title": "Bonnes pratiques en cybersecurite pour les PME",
                "excerpt": "Mesures simples a forte valeur: MFA, sauvegardes, mises a jour, sensibilisation.",
                "body": "La securite est un processus, pas un produit. Quelques pratiques apportent 80% du benefice pour un effort raisonnable:\n\n1) Activer la double authentification (MFA) pour tous les acces sensibles.\n2) Sauvegardes regulieres et tests de restauration.\n3) Mise a jour systematique des systemes et dependances.\n4) Sensibilisation des equipes (phishing, mots de passe, partage).\n5) Principe du moindre privilege et revue des acces trimestrielle.\n\nCouplees a une supervision basique (logs, alertes), ces mesures reduisent fortement le risque.",
            },
        ]

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
                obj.title = a["title"]
                obj.excerpt = a["excerpt"]
                obj.body = a["body"]
                obj.is_published = True
                obj.save()

            status = "cree" if created else "mis a jour"
            self.stdout.write(self.style.SUCCESS(f"Article {status}: {a['slug']}"))

        self.stdout.write(self.style.SUCCESS("Termine. Ajoutez les images via l'admin Django."))
