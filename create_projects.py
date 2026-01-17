"""Script pour créer les projets portfolio EEBC et Nettoyage Express."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.portfolio.models import Project, ProjectType

# Projet 1: EEBC
eebc, created = Project.objects.update_or_create(
    slug='eebc-expertise-comptable',
    defaults={
        'title': 'EEBC - Cabinet Expertise Comptable',
        'project_type': ProjectType.VITRINE,
        'client_name': 'EEBC (Expertise et Etudes du Bassin du Congo)',
        'objective': 'Créer une présence en ligne professionnelle pour un cabinet d\'expertise comptable basé en Afrique centrale. Le site devait refléter le sérieux et la fiabilité du cabinet tout en présentant clairement leurs services.',
        'solution': 'Développement d\'un site vitrine moderne avec une identité visuelle forte. Intégration d\'un formulaire de contact intelligent, présentation des services (audit, fiscalité, conseil), et mise en avant de l\'équipe d\'experts.',
        'result': 'Augmentation de 150% des demandes de contact en ligne. Le site positionne EEBC comme un acteur majeur de l\'expertise comptable dans la région, avec une image moderne et professionnelle.',
        'technologies': ['Django', 'HTMX', 'PostgreSQL', 'WeasyPrint', 'Brevo'],
        'url': 'https://eglise-ebc.org',
        'is_featured': True,
        'is_published': True
    }
)
status = "créé" if created else "mis à jour"
print(f'EEBC: {status} - {eebc.url}')

# Projet 2: Nettoyage Express
nettoyage, created = Project.objects.update_or_create(
    slug='nettoyage-express-services',
    defaults={
        'title': 'Nettoyage Express - Services de Propreté',
        'project_type': ProjectType.SYSTEME,
        'client_name': 'Nettoyage Express SARL',
        'objective': 'Digitaliser la gestion complète d\'une entreprise de nettoyage : devis automatisés, planning des équipes, facturation et suivi client. Remplacer les processus papier par une solution tout-en-un.',
        'solution': 'Création d\'une plateforme web sur-mesure intégrant : générateur de devis PDF personnalisés, tableau de bord planning avec affectation des équipes, module de facturation automatique, et espace client pour le suivi des interventions.',
        'result': 'Gain de temps de 40% sur l\'administratif. Réduction des erreurs de facturation à zéro. Satisfaction client améliorée grâce au suivi en temps réel des interventions.',
        'technologies': ['Django', 'HTMX', 'PostgreSQL', 'WeasyPrint', 'Chart.js', 'Stripe'],
        'url': 'https://nettoyageexpresse.fr',
        'is_featured': True,
        'is_published': True
    }
)
status = "créé" if created else "mis à jour"
print(f'Nettoyage Express: {status} - {nettoyage.url}')

print(f'\nTotal projets portfolio: {Project.objects.count()}')
for p in Project.objects.all():
    print(f'  - {p.title}: {p.url}')
