"""Script pour ajouter des projets de démonstration au portfolio."""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.portfolio.models import Project, ProjectType

DEMO_PROJECTS = [
    {
        'slug': 'boutique-creole-luxury',
        'title': 'Boutique Créole Luxury',
        'project_type': ProjectType.COMMERCE,
        'client_name': 'Boutique Créole',
        'objective': 'Créer une boutique e-commerce premium pour vendre des produits artisanaux guyanais de luxe à une clientèle internationale.',
        'solution': 'Développement d\'une plateforme e-commerce sur-mesure avec intégration Stripe, gestion des stocks en temps réel, et expédition internationale automatisée.',
        'result': 'Augmentation de 340% des ventes en ligne et expansion vers les marchés européens et nord-américains.',
        'technologies': ['Django', 'Python', 'Stripe', 'HTMX', 'TailwindCSS', 'PostgreSQL', 'Redis'],
        'url': 'https://boutique-creole.gf',
        'is_published': True,
        'is_featured': True,
    },
    {
        'slug': 'gestion-flotte-amazonie',
        'title': 'GFA - Gestion Flotte Amazonie',
        'project_type': ProjectType.SYSTEME,
        'client_name': 'Transport Amazonie SAS',
        'objective': 'Développer un ERP complet pour la gestion d\'une flotte de véhicules et pirogues en zone amazonienne avec suivi GPS temps réel.',
        'solution': 'Plateforme sur-mesure avec tracking GPS, maintenance prédictive, gestion des chauffeurs/pilotes, et tableau de bord analytique avancé.',
        'result': 'Réduction de 45% des coûts de maintenance et amélioration de 60% de l\'efficacité logistique.',
        'technologies': ['Django', 'Python', 'PostgreSQL', 'PostGIS', 'Leaflet', 'WebSocket', 'Celery'],
        'url': '',
        'is_published': True,
        'is_featured': True,
    },
    {
        'slug': 'restaurant-le-maroni',
        'title': 'Restaurant Le Maroni',
        'project_type': ProjectType.VITRINE,
        'client_name': 'Le Maroni Gastronomique',
        'objective': 'Créer un site vitrine élégant pour un restaurant gastronomique mettant en valeur la cuisine fusion amazonienne.',
        'solution': 'Site web immersif avec réservation en ligne, menu interactif, galerie photos professionnelles et intégration Google Business.',
        'result': 'Augmentation de 180% des réservations en ligne et amélioration significative de la visibilité locale.',
        'technologies': ['Django', 'Python', 'HTMX', 'TailwindCSS', 'SQLite'],
        'url': 'https://lemaroni.gf',
        'is_published': True,
        'is_featured': False,
    },
    {
        'slug': 'clinique-veterinaire-cayenne',
        'title': 'Clinique Vétérinaire de Cayenne',
        'project_type': ProjectType.SYSTEME,
        'client_name': 'Dr. Marie Laurent',
        'objective': 'Digitaliser entièrement la gestion d\'une clinique vétérinaire : rendez-vous, dossiers patients, facturation et rappels vaccins.',
        'solution': 'Développement d\'un ERP médical vétérinaire avec prise de rendez-vous en ligne, suivi des animaux, ordonnances électroniques et rappels automatisés.',
        'result': 'Gain de 3h/jour en tâches administratives et satisfaction client en hausse de 95%.',
        'technologies': ['Django', 'Python', 'PostgreSQL', 'Celery', 'Brevo', 'HTMX'],
        'url': '',
        'is_published': True,
        'is_featured': False,
    },
    {
        'slug': 'agence-immobiliere-kourou',
        'title': 'Immo Spatial Kourou',
        'project_type': ProjectType.VITRINE,
        'client_name': 'Immo Spatial',
        'objective': 'Développer une vitrine immobilière moderne avec recherche avancée et visite virtuelle 360° des biens.',
        'solution': 'Plateforme immobilière avec filtres de recherche intelligents, intégration visite virtuelle, alertes email personnalisées et estimation automatique.',
        'result': 'Doublement des demandes de visite et réduction du temps moyen de vente de 40%.',
        'technologies': ['Django', 'Python', 'PostgreSQL', 'Matterport API', 'Mapbox', 'HTMX'],
        'url': 'https://immospatial.gf',
        'is_published': True,
        'is_featured': False,
    },
    {
        'slug': 'marketplace-artisans-guyane',
        'title': 'Artisans de Guyane',
        'project_type': ProjectType.COMMERCE,
        'client_name': 'Collectif Artisans 973',
        'objective': 'Créer une marketplace pour les artisans guyanais permettant la vente directe aux consommateurs locaux et internationaux.',
        'solution': 'Marketplace multi-vendeurs avec gestion des boutiques individuelles, paiement sécurisé, système d\'avis et expédition intégrée.',
        'result': 'Plus de 150 artisans inscrits et 2000+ produits vendus dans les 6 premiers mois.',
        'technologies': ['Django', 'Python', 'PostgreSQL', 'Stripe Connect', 'Colissimo API', 'AWS S3'],
        'url': 'https://artisans-guyane.fr',
        'is_published': True,
        'is_featured': True,
    },
]

print("🚀 Ajout des projets de démonstration au portfolio...\n")

for project_data in DEMO_PROJECTS:
    project, created = Project.objects.get_or_create(
        slug=project_data['slug'],
        defaults=project_data
    )
    status = "✅ Créé" if created else "ℹ️  Existe déjà"
    print(f"{status}: {project.title} ({project.get_project_type_display()})")

print(f"\n{'='*50}")
print(f"📊 Total projets publiés: {Project.objects.filter(is_published=True).count()}")
print(f"⭐ Projets featured: {Project.objects.filter(is_featured=True).count()}")
print("✨ Import terminé!")
