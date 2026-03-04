from __future__ import annotations

from django.conf import settings


def captcha_settings(request):
    """Inject captcha keys and GA4 measurement ID into template context."""
    turnstile_site_key = getattr(settings, 'TURNSTILE_SITE_KEY', '')
    recaptcha_site_key = getattr(settings, 'RECAPTCHA_SITE_KEY', '')
    timeout_ms = getattr(settings, 'TURNSTILE_FALLBACK_TIMEOUT_MS', 2500)
    try:
        timeout_ms = int(timeout_ms)
    except (TypeError, ValueError):
        timeout_ms = 2500

    return {
        'turnstile_site_key': turnstile_site_key,
        'recaptcha_site_key': recaptcha_site_key,
        'turnstile_fallback_timeout_ms': timeout_ms,
        'ga4_measurement_id': getattr(settings, 'GA4_MEASUREMENT_ID', ''),
    }


def breadcrumbs(request):
    """
    Generate breadcrumbs based on URL path for SEO Schema.org markup.
    
    Returns breadcrumbs_list for use with breadcrumb_schema.html partial.
    Enables Google Rich Snippets breadcrumb display (+4 SEO points).
    
    Example output:
        {'breadcrumbs_list': [
            {'name': 'Accueil', 'url': '/'},
            {'name': 'Nos Services', 'url': '/services/'},
        ]}
    """
    path = request.path.strip('/').split('/')
    breadcrumbs_list = [{'name': 'Accueil', 'url': '/'}]
    
    # Mapping URL segments → French display names
    url_names = {
        # Pages principales
        'services': 'Nos Services',
        'methode': 'Notre Méthode',
        'portfolio': 'Nos signatures',
        'chroniques': 'Chroniques TUS',
        'contact': 'Contact',
        'apropos': 'À Propos',
        
        # Pages légales
        'mentions-legales': 'Mentions Légales',
        'politique-confidentialite': 'Politique de Confidentialité',
        'cgv': 'Conditions Générales de Vente',
        'faq': 'Questions Fréquentes',
        
        # Services détaillés
        'developpement-web': 'Développement Web',
        'site-vitrine': 'Site Vitrine',
        'site-ecommerce': 'Site E-commerce',
        'application-metier': 'Application Métier',
        'refonte': 'Refonte de Site',
        'maintenance': 'Maintenance & Support',
        
        # Gestion clients (Écosystème TUS)
        'ecosysteme-tus': 'Écosystème TUS',
        'tableau-de-bord': 'Tableau de Bord',
        'devis': 'Devis',
        'factures': 'Factures',
        'projets': 'Mes Projets',
        
        # Chroniques catégories
        'tutoriels': 'Tutoriels',
        'actualites': 'Actualités',
        'case-studies': 'Études de Cas',
    }
    
    current_url = ''
    for i, segment in enumerate(path):
        if not segment:
            continue
        
        current_url += f'/{segment}'
        
        # Get French name or fallback to capitalized segment
        name = url_names.get(segment, segment.replace('-', ' ').replace('_', ' ').title())
        
        # Don't add numeric IDs (like /chroniques/123/) to breadcrumbs
        if segment.isdigit():
            continue
            
        breadcrumbs_list.append({'name': name, 'url': current_url + '/'})
    
    return {'breadcrumbs_list': breadcrumbs_list}

