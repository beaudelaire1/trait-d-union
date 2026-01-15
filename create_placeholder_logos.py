import os
import sys
import django

# Configuration Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.portfolio.models import Project
from django.core.files.base import ContentFile

def create_placeholder_logo(name, initials, color="#3B82F6"):
    """Crée un logo SVG placeholder"""
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="400" height="400" viewBox="0 0 400 400">
    <rect width="400" height="400" fill="{color}"/>
    <text x="200" y="200" font-family="Arial, sans-serif" font-size="120" font-weight="bold" 
          fill="white" text-anchor="middle" dominant-baseline="middle">{initials}</text>
</svg>'''
    return svg.encode('utf-8')

def main():
    print("🎨 Création des logos placeholder\n")
    
    # EEBC
    print("1. EEBC (Église Évangélique Baptiste de Cabassou)")
    try:
        project = Project.objects.get(slug='eglise-evangelique-baptiste-cabassou')
        logo_svg = create_placeholder_logo("EEBC", "EEBC", "#8B5CF6")
        project.thumbnail.save('eebc-logo.svg', ContentFile(logo_svg), save=True)
        print(f"✓ Logo créé: {project.thumbnail.url}")
    except Exception as e:
        print(f"✗ Erreur: {e}")
    
    print()
    
    # Nettoyage Express
    print("2. Nettoyage Express")
    try:
        project = Project.objects.get(slug='nettoyage-express')
        logo_svg = create_placeholder_logo("Nettoyage Express", "NE", "#10B981")
        project.thumbnail.save('nettoyage-express-logo.svg', ContentFile(logo_svg), save=True)
        print(f"✓ Logo créé: {project.thumbnail.url}")
    except Exception as e:
        print(f"✗ Erreur: {e}")
    
    print("\n✅ Logos placeholder créés!")
    print("\nVous pouvez les remplacer par les vrais logos via l'admin à /tus-manager/portfolio/project/")

if __name__ == '__main__':
    main()
