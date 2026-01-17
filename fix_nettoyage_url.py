import os
import sys
import django
import requests
from pathlib import Path

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.portfolio.models import Project
from django.core.files.base import ContentFile

def download_and_save_logo(url, project_slug):
    """Télécharge un logo et le sauvegarde pour un projet"""
    try:
        print(f"📥 Téléchargement du logo depuis {url}...")
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        # Déterminer l'extension
        content_type = response.headers.get('content-type', '')
        if 'png' in content_type:
            ext = 'png'
        elif 'svg' in content_type:
            ext = 'svg'
        elif 'jpeg' in content_type or 'jpg' in content_type:
            ext = 'jpg'
        else:
            ext = 'png'
        
        filename = f"{project_slug}.{ext}"
        
        # Récupérer le projet
        project = Project.objects.get(slug=project_slug)
        
        # Sauvegarder le fichier
        project.thumbnail.save(filename, ContentFile(response.content), save=True)
        
        print(f"✓ Logo sauvegardé: {project.thumbnail.url}")
        return True
        
    except Exception as e:
        print(f"✗ Erreur: {e}")
        return False

def main():
    print("🔧 Correction de l'URL Nettoyage Express\n")
    
    # Corriger l'URL
    try:
        project = Project.objects.get(slug='nettoyage-express')
        project.website_url = 'https://nettoyageexpresse.fr'
        project.save()
        print("✓ URL corrigée: nettoyageexpresse.fr\n")
    except Exception as e:
        print(f"✗ Erreur lors de la mise à jour: {e}\n")
    
    # Essayer de télécharger les logos
    print("1. EEBC")
    eebc_urls = [
        'https://eglise-ebc.org/favicon.ico',
        'https://eglise-ebc.org/logo.png',
        'https://eglise-ebc.org/static/images/logo.png',
        'https://eglise-ebc.org/media/logo.png'
    ]
    
    for url in eebc_urls:
        if download_and_save_logo(url, 'eglise-evangelique-baptiste-cabassou'):
            break
    
    print("\n2. Nettoyage Express")
    nettoyage_urls = [
        'https://nettoyageexpresse.fr/favicon.ico',
        'https://nettoyageexpresse.fr/logo.png',
        'https://nettoyageexpresse.fr/static/logo.png',
        'https://nettoyageexpresse.fr/static/images/logo.png',
        'https://nettoyageexpresse.fr/media/logo.png',
        'https://nettoyageexpresse.fr/assets/logo.png'
    ]
    
    for url in nettoyage_urls:
        if download_and_save_logo(url, 'nettoyage-express'):
            break
    
    print("\n✅ Script terminé!")

if __name__ == '__main__':
    main()
