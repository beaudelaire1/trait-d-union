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
from django.conf import settings

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
            ext = 'png'  # par défaut
        
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
    print("🎨 Ajout des logos aux projets portfolio\n")
    
    # EEBC - Essayer plusieurs URLs possibles
    eebc_urls = [
        'https://eglise-ebc.org/favicon.ico',
        'https://eglise-ebc.org/logo.png',
        'https://eglise-ebc.org/static/logo.png',
        'https://eglise-ebc.org/assets/logo.png'
    ]
    
    print("1. EEBC (Église Évangélique Baptiste de Cabassou)")
    success = False
    for url in eebc_urls:
        if download_and_save_logo(url, 'eglise-evangelique-baptiste-cabassou'):
            success = True
            break
    
    if not success:
        print("⚠ Impossible de télécharger le logo EEBC automatiquement")
    
    print()
    
    # Nettoyage Express
    nettoyage_urls = [
        'https://nettoyageexpress.fr/favicon.ico',
        'https://nettoyageexpress.fr/logo.png',
        'https://nettoyageexpress.fr/static/logo.png',
        'https://nettoyageexpress.fr/assets/logo.png'
    ]
    
    print("2. Nettoyage Express")
    success = False
    for url in nettoyage_urls:
        if download_and_save_logo(url, 'nettoyage-express'):
            success = True
            break
    
    if not success:
        print("⚠ Impossible de télécharger le logo Nettoyage Express automatiquement")
    
    print("\n✅ Script terminé!")
    print("\nNote: Si les logos n'ont pas pu être téléchargés automatiquement,")
    print("vous pouvez les ajouter manuellement via l'admin Django à /tus-manager/")

if __name__ == '__main__':
    main()
