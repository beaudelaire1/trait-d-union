import os
import sys
import django

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.portfolio.models import Project

def main():
    print("🔧 Correction de l'URL Nettoyage Express\n")
    
    try:
        project = Project.objects.get(slug='nettoyage-express')
        old_url = project.url
        project.url = 'https://nettoyageexpresse.fr'
        project.save()
        print(f"✓ URL mise à jour:")
        print(f"  Ancien: {old_url}")
        print(f"  Nouveau: {project.url}")
    except Project.DoesNotExist:
        print("✗ Projet 'nettoyage-express' non trouvé")
    except Exception as e:
        print(f"✗ Erreur: {e}")

if __name__ == '__main__':
    main()
