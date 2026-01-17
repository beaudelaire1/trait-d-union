"""Script pour ajouter les services de design graphique en base de données."""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from services.models import ServiceCategory, Service


def main():
    print("🎨 Ajout des services de Design Graphique\n")
    
    # Créer la catégorie Design Graphique
    category, created = ServiceCategory.objects.get_or_create(
        slug='design-graphique',
        defaults={
            'name': 'Design Graphique',
            'description': 'Services de création graphique : logos, identités visuelles, supports print et digitaux.',
            'icon': 'palette',
            'order': 1,  # Premier dans la liste
        }
    )
    if created:
        print(f"✓ Catégorie créée: {category.name}")
    else:
        print(f"✓ Catégorie existante: {category.name}")
    
    # Liste des services de design graphique
    design_services = [
        {
            'slug': 'logo-identite-visuelle',
            'name': 'Logo & Identité Visuelle',
            'description': 'Création de logo professionnel et charte graphique complète. Inclut le logo en différents formats, palette de couleurs, typographies et guide d\'utilisation.',
            'short_description': 'Création de logo et charte graphique complète.',
            'base_price': Decimal('800.00'),
            'price_unit': 'forfait',
            'is_featured': True,
        },
        {
            'slug': 'supports-print',
            'name': 'Supports Print',
            'description': 'Conception de supports imprimés professionnels : cartes de visite, flyers, brochures, affiches, dépliants. Design sur-mesure adapté à votre identité visuelle.',
            'short_description': 'Cartes de visite, flyers, brochures, affiches.',
            'base_price': Decimal('150.00'),
            'price_unit': 'pièce',
            'is_featured': False,
        },
        {
            'slug': 'visuels-reseaux-sociaux',
            'name': 'Visuels Réseaux Sociaux',
            'description': 'Création de visuels optimisés pour les réseaux sociaux : bannières, posts, stories, kits de communication. Templates personnalisables inclus.',
            'short_description': 'Visuels, bannières et kits de communication.',
            'base_price': Decimal('300.00'),
            'price_unit': 'pack',
            'is_featured': True,
        },
        {
            'slug': 'packaging-design',
            'name': 'Packaging & Étiquettes',
            'description': 'Design d\'emballages et étiquettes produits. Conception créative qui met en valeur vos produits et renforce votre image de marque.',
            'short_description': 'Design d\'emballages et étiquettes produits.',
            'base_price': Decimal('500.00'),
            'price_unit': 'forfait',
            'is_featured': False,
        },
        {
            'slug': 'illustrations-personnalisees',
            'name': 'Illustrations Personnalisées',
            'description': 'Création d\'illustrations sur-mesure pour vos projets web, print ou communication. Style adapté à votre univers de marque.',
            'short_description': 'Illustrations sur-mesure pour web et print.',
            'base_price': Decimal('250.00'),
            'price_unit': 'illustration',
            'is_featured': False,
        },
        {
            'slug': 'refonte-identite',
            'name': 'Refonte d\'Identité Visuelle',
            'description': 'Modernisation complète de votre identité visuelle existante. Analyse de l\'existant, propositions créatives et déploiement sur tous vos supports.',
            'short_description': 'Modernisation complète de votre identité.',
            'base_price': Decimal('1500.00'),
            'price_unit': 'forfait',
            'is_featured': True,
        },
    ]
    
    # Créer les services
    for service_data in design_services:
        service, created = Service.objects.get_or_create(
            slug=service_data['slug'],
            defaults={
                'category': category,
                'name': service_data['name'],
                'description': service_data['description'],
                'short_description': service_data['short_description'],
                'base_price': service_data['base_price'],
                'price_unit': service_data['price_unit'],
                'is_active': True,
                'is_featured': service_data['is_featured'],
            }
        )
        if created:
            print(f"  ✓ Service créé: {service.name} ({service.base_price}€/{service.price_unit})")
        else:
            print(f"  ✓ Service existant: {service.name}")
    
    print(f"\n✅ Import terminé!")
    print(f"Total catégories: {ServiceCategory.objects.count()}")
    print(f"Total services: {Service.objects.count()}")
    print(f"Services Design Graphique: {Service.objects.filter(category=category).count()}")


if __name__ == '__main__':
    main()
