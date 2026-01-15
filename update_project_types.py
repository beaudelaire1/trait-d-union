"""Mise à jour des types de projets EEBC et Nettoyage Express."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.portfolio.models import Project, ProjectType

# Mise à jour EEBC
eebc = Project.objects.get(slug='eglise-evangelique-baptiste-cabassou')
eebc.project_type = ProjectType.SYSTEME
eebc.objective = 'Créer une présence en ligne pour l\'église avec un site vitrine public couplé à un ERP complet pour la gestion de la communauté.'
eebc.solution = 'Développement d\'une plateforme intégrée : site vitrine moderne pour la communication publique et ERP personnalisé pour la gestion des membres, événements, finances et communications internes.'
eebc.result = 'Plateforme complète permettant à l\'église de communiquer avec sa communauté via le site public tout en gérant efficacement ses activités administratives et pastorales via l\'ERP intégré.'
eebc.save()
print(f'✓ EEBC mis à jour: {eebc.project_type}')

# Mise à jour Nettoyage Express
nettoyage = Project.objects.get(slug='nettoyage-express')
nettoyage.project_type = ProjectType.SYSTEME
nettoyage.objective = 'Développer une solution complète avec site vitrine pour la promotion des services et ERP intégré pour la gestion opérationnelle.'
nettoyage.solution = 'Plateforme web intégrée combinant un site vitrine responsive pour présenter les services de nettoyage et un ERP pour gérer les clients, devis, réservations, planning des interventions et facturation.'
nettoyage.result = 'Solution complète permettant à Nettoyage Express de promouvoir ses services en ligne tout en gérant l\'intégralité de son activité opérationnelle via un ERP sur mesure.'
nettoyage.save()
print(f'✓ Nettoyage Express mis à jour: {nettoyage.project_type}')

print('\n✅ Types de projets mis à jour!')
print(f'EEBC: {eebc.get_project_type_display()}')
print(f'Nettoyage Express: {nettoyage.get_project_type_display()}')
