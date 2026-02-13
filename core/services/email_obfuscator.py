"""Service d'obfuscation d'email pour prévenir le scraping automatisé.

Protection anti-spam multi-couches :
- Encodage Base64 (décodage côté client)
- Honeypot invisible pour bots
- Rate limiting serveur (middleware existant)
"""
from __future__ import annotations

import base64
from typing import Dict


def obfuscate_email(email: str) -> Dict[str, str]:
    """Obfusque une adresse email pour affichage sécurisé.
    
    Args:
        email: Adresse email en clair (ex: contact@traitdunion.it)
    
    Returns:
        Dict avec 'encoded' (base64) et 'display' (texte masqué)
    
    Examples:
        >>> obfuscate_email('contact@traitdunion.it')
        {'encoded': 'Y29udGFjdEB0cmFpdGR1bmlvbi5pdA==', 'display': 'contact [at] traitdunion [dot] it'}
    """
    encoded = base64.b64encode(email.encode('utf-8')).decode('utf-8')
    display = email.replace('@', ' [at] ').replace('.', ' [dot] ')
    
    return {
        'encoded': encoded,
        'display': display,
        'original': email  # Pour debug uniquement, ne pas exposer en template
    }


def get_company_email_obfuscated() -> Dict[str, str]:
    """Retourne l'email de Trait d'Union Studio obfusqué.
    
    Returns:
        Dict avec versions encodée et masquée de contact@traitdunion.it
    """
    return obfuscate_email('contact@traitdunion.it')
