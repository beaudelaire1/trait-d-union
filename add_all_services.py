"""Script pour ajouter tous les services détaillés en base de données."""
import os
import django
from decimal import Decimal

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from services.models import ServiceCategory, Service


def main():
    print("🚀 Ajout de tous les services détaillés\n")
    
    # ==================== DESIGN GRAPHIQUE ====================
    design_category, created = ServiceCategory.objects.get_or_create(
        slug='design-graphique',
        defaults={
            'name': 'Design Graphique',
            'description': 'Services de création graphique : logos, identités visuelles, supports print et digitaux.',
            'icon': 'palette',
            'order': 1,
        }
    )
    print(f"{'✓ Créé' if created else '• Existant'}: Catégorie {design_category.name}")
    
    design_services = [
        {'slug': 'logo-identite-visuelle', 'name': 'Logo & Identité Visuelle', 'short_description': 'Création de logo et charte graphique complète.', 'description': 'Création de logo professionnel et charte graphique complète. Inclut le logo en différents formats, palette de couleurs, typographies et guide d\'utilisation.', 'base_price': Decimal('800.00'), 'price_unit': 'forfait', 'is_featured': True},
        {'slug': 'supports-print', 'name': 'Supports Print', 'short_description': 'Cartes de visite, flyers, brochures, affiches.', 'description': 'Conception de supports imprimés professionnels : cartes de visite, flyers, brochures, affiches, dépliants. Design sur-mesure adapté à votre identité visuelle.', 'base_price': Decimal('150.00'), 'price_unit': 'pièce', 'is_featured': False},
        {'slug': 'visuels-reseaux-sociaux', 'name': 'Visuels Réseaux Sociaux', 'short_description': 'Visuels, bannières et kits de communication.', 'description': 'Création de visuels optimisés pour les réseaux sociaux : bannières, posts, stories, kits de communication. Templates personnalisables inclus.', 'base_price': Decimal('300.00'), 'price_unit': 'pack', 'is_featured': True},
        {'slug': 'packaging-design', 'name': 'Packaging & Étiquettes', 'short_description': 'Design d\'emballages et étiquettes produits.', 'description': 'Design d\'emballages et étiquettes produits. Conception créative qui met en valeur vos produits et renforce votre image de marque.', 'base_price': Decimal('500.00'), 'price_unit': 'forfait', 'is_featured': False},
    ]
    
    for data in design_services:
        service, created = Service.objects.update_or_create(
            slug=data['slug'],
            defaults={**data, 'category': design_category, 'is_active': True}
        )
        print(f"  {'✓' if created else '•'} {service.name}: {service.base_price}€")
    
    # ==================== SITE VITRINE ====================
    vitrine_category, created = ServiceCategory.objects.get_or_create(
        slug='site-vitrine',
        defaults={
            'name': 'Site Vitrine',
            'description': 'Sites web élégants et performants pour présenter votre activité.',
            'icon': 'globe',
            'order': 2,
        }
    )
    print(f"\n{'✓ Créé' if created else '• Existant'}: Catégorie {vitrine_category.name}")
    
    vitrine_services = [
        {'slug': 'site-one-page', 'name': 'Site One Page', 'short_description': 'Page unique optimisée, idéale pour lancer rapidement.', 'description': 'Site web d\'une seule page optimisée, parfait pour présenter rapidement votre activité ou un produit spécifique. Design moderne, responsive et optimisé SEO.', 'base_price': Decimal('1500.00'), 'price_unit': 'forfait', 'is_featured': False},
        {'slug': 'site-vitrine-standard', 'name': 'Vitrine Standard', 'short_description': '5-10 pages, blog intégré, formulaire contact.', 'description': 'Site vitrine complet de 5 à 10 pages avec blog intégré, formulaire de contact, et optimisation SEO. Parfait pour les PME et professionnels.', 'base_price': Decimal('3000.00'), 'price_unit': 'forfait', 'is_featured': True},
        {'slug': 'site-vitrine-premium', 'name': 'Vitrine Premium', 'short_description': 'Design sur-mesure, animations, multilangue.', 'description': 'Site vitrine haut de gamme avec design sur-mesure, animations premium, support multilangue et fonctionnalités avancées. L\'excellence pour votre image.', 'base_price': Decimal('5500.00'), 'price_unit': 'forfait', 'is_featured': True},
        {'slug': 'refonte-site', 'name': 'Refonte de Site', 'short_description': 'Modernisation complète de votre site existant.', 'description': 'Modernisation complète de votre site web existant : nouveau design, amélioration des performances, migration de contenu et optimisation SEO.', 'base_price': Decimal('2500.00'), 'price_unit': 'forfait', 'is_featured': False},
    ]
    
    for data in vitrine_services:
        service, created = Service.objects.update_or_create(
            slug=data['slug'],
            defaults={**data, 'category': vitrine_category, 'is_active': True}
        )
        print(f"  {'✓' if created else '•'} {service.name}: {service.base_price}€")
    
    # ==================== E-COMMERCE ====================
    ecommerce_category, created = ServiceCategory.objects.get_or_create(
        slug='e-commerce',
        defaults={
            'name': 'E-commerce',
            'description': 'Boutiques en ligne optimisées pour la conversion et la fidélisation.',
            'icon': 'shopping-cart',
            'order': 3,
        }
    )
    print(f"\n{'✓ Créé' if created else '• Existant'}: Catégorie {ecommerce_category.name}")
    
    ecommerce_services = [
        {'slug': 'boutique-starter', 'name': 'Boutique Starter', 'short_description': 'Jusqu\'à 50 produits, paiement Stripe/PayPal.', 'description': 'Boutique en ligne pour débuter avec jusqu\'à 50 produits. Paiement sécurisé Stripe/PayPal, gestion des commandes et notifications email.', 'base_price': Decimal('5000.00'), 'price_unit': 'forfait', 'is_featured': False},
        {'slug': 'boutique-pro', 'name': 'Boutique Pro', 'short_description': 'Illimité, gestion stocks, multi-devises.', 'description': 'Boutique e-commerce professionnelle sans limite de produits. Gestion avancée des stocks, multi-devises, promotions et programme de fidélité.', 'base_price': Decimal('8000.00'), 'price_unit': 'forfait', 'is_featured': True},
        {'slug': 'marketplace', 'name': 'Marketplace', 'short_description': 'Multi-vendeurs, commissions, dashboard vendeurs.', 'description': 'Plateforme marketplace multi-vendeurs complète. Système de commissions, tableau de bord vendeurs, validation produits et gestion des litiges.', 'base_price': Decimal('18000.00'), 'price_unit': 'forfait', 'is_featured': False},
        {'slug': 'click-collect', 'name': 'Click & Collect', 'short_description': 'Commande en ligne, retrait en magasin.', 'description': 'Solution Click & Collect pour commerces avec points de vente. Commande en ligne, gestion des créneaux de retrait et notifications SMS.', 'base_price': Decimal('6500.00'), 'price_unit': 'forfait', 'is_featured': False},
    ]
    
    for data in ecommerce_services:
        service, created = Service.objects.update_or_create(
            slug=data['slug'],
            defaults={**data, 'category': ecommerce_category, 'is_active': True}
        )
        print(f"  {'✓' if created else '•'} {service.name}: {service.base_price}€")
    
    # ==================== PLATEFORME & ERP ====================
    plateforme_category, created = ServiceCategory.objects.get_or_create(
        slug='plateforme-erp',
        defaults={
            'name': 'Plateforme & ERP',
            'description': 'Outils métier sur mesure pour automatiser vos processus.',
            'icon': 'cog',
            'order': 4,
        }
    )
    print(f"\n{'✓ Créé' if created else '• Existant'}: Catégorie {plateforme_category.name}")
    
    plateforme_services = [
        {'slug': 'crm-sur-mesure', 'name': 'CRM Sur Mesure', 'short_description': 'Gestion clients, leads, pipeline commercial.', 'description': 'CRM personnalisé pour gérer vos clients, leads et pipeline commercial. Automatisation des relances, reporting et intégration email.', 'base_price': Decimal('12000.00'), 'price_unit': 'forfait', 'is_featured': False},
        {'slug': 'mini-erp', 'name': 'Mini-ERP', 'short_description': 'Devis, factures, stocks, comptabilité simplifiée.', 'description': 'Solution ERP complète pour PME : gestion des devis, factures, stocks, achats et comptabilité simplifiée. Tableau de bord analytique inclus.', 'base_price': Decimal('15000.00'), 'price_unit': 'forfait', 'is_featured': True},
        {'slug': 'portail-client', 'name': 'Portail Client', 'short_description': 'Espace sécurisé, suivi projets, documents.', 'description': 'Portail client sécurisé pour le suivi de projets, partage de documents, messagerie et historique des échanges. Améliore la relation client.', 'base_price': Decimal('8000.00'), 'price_unit': 'forfait', 'is_featured': False},
        {'slug': 'api-integrations', 'name': 'API & Intégrations', 'short_description': 'Connectez vos outils, automatisez vos flux.', 'description': 'Développement d\'API et intégrations pour connecter vos outils existants. Automatisation des flux de données et synchronisation temps réel.', 'base_price': Decimal('3000.00'), 'price_unit': 'forfait', 'is_featured': False},
    ]
    
    for data in plateforme_services:
        service, created = Service.objects.update_or_create(
            slug=data['slug'],
            defaults={**data, 'category': plateforme_category, 'is_active': True}
        )
        print(f"  {'✓' if created else '•'} {service.name}: {service.base_price}€")
    
    # ==================== RÉSUMÉ ====================
    print("\n" + "="*50)
    print("✅ Import terminé!")
    print(f"   Total catégories: {ServiceCategory.objects.count()}")
    print(f"   Total services: {Service.objects.count()}")
    print("\n📊 Détail par catégorie:")
    for cat in ServiceCategory.objects.all().order_by('order'):
        count = Service.objects.filter(category=cat).count()
        print(f"   • {cat.name}: {count} services")


if __name__ == '__main__':
    main()
