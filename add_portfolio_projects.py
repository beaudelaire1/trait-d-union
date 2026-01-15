"""Script pour ajouter les projets portfolio EEBC et Nettoyage Express."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.portfolio.models import Project, ProjectType

# Projet 1: EEBC
eebc, created = Project.objects.get_or_create(
    slug='eglise-evangelique-baptiste-cabassou',
    defaults={
        'title': 'Eglise Evangélique Baptiste de Cabassou',
        'project_type': ProjectType.VITRINE,
        'client_name': 'EEBC',
        'objective': 'Créer une présence en ligne pour l\'église avec un site vitrine moderne et un espace de gestion interne (ERP) pour la communauté.',
        'solution': 'Développement d\'un site vitrine public présentant les activités de l\'église, complété par un système ERP personnalisé pour la gestion des membres, événements et communications internes.',
        'result': 'Site web professionnel permettant à l\'église de communiquer efficacement avec sa communauté et de gérer ses activités administratives de manière centralisée.',
        'technologies': ['Django', 'Python', 'HTML/CSS', 'JavaScript', 'PostgreSQL'],
        'url': 'https://eglise-ebc.org',
        'is_published': True,
        'is_featured': True,
    }
)
if created:
    print(f'✓ Projet EEBC créé: {eebc.title}')
else:
    print(f'✓ Projet EEBC existe déjà: {eebc.title}')

# Projet 2: Nettoyage Express
nettoyage, created = Project.objects.get_or_create(
    slug='nettoyage-express',
    defaults={
        'title': 'Nettoyage Express',
        'project_type': ProjectType.VITRINE,
        'client_name': 'Nettoyage Express',
        'objective': 'Développer un site vitrine moderne pour promouvoir les services de nettoyage professionnel avec un système de gestion intégré.',
        'solution': 'Site vitrine responsive présentant les services de nettoyage, accompagné d\'un ERP pour la gestion des clients, réservations et plannings des interventions.',
        'result': 'Plateforme web complète permettant à Nettoyage Express de présenter ses services en ligne et de gérer efficacement son activité opérationnelle.',
        'technologies': ['Django', 'Python', 'HTML/CSS', 'JavaScript', 'Bootstrap', 'PostgreSQL'],
        'url': 'https://nettoyageexpress.fr',
        'is_published': True,
        'is_featured': True,
    }
)
if created:
    print(f'✓ Projet Nettoyage Express créé: {nettoyage.title}')
else:
    print(f'✓ Projet Nettoyage Express existe déjà: {nettoyage.title}')

print('\n✅ Import terminé!')
print(f'Total projets: {Project.objects.count()}')
