"""
Signals pour l'application Portfolio.

Conversion automatique des images uploadées en WebP.
"""
import logging

from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import Project, ProjectImage

logger = logging.getLogger(__name__)


def convert_image_to_webp(instance, field_name: str) -> None:
    """
    Convertit une image en WebP si elle n'est pas déjà en WebP.
    
    Args:
        instance: Instance du modèle Django
        field_name: Nom du champ ImageField
    """
    from core.services.image_processor import image_processor
    
    image_field = getattr(instance, field_name, None)
    if not image_field:
        return
    
    # Vérifier si l'image est nouvelle ou modifiée
    if not hasattr(image_field, 'file'):
        return
    
    # Ne pas reconvertir les WebP
    filename = getattr(image_field, 'name', '')
    if filename.lower().endswith('.webp'):
        logger.debug(f"Image déjà en WebP: {filename}")
        return
    
    # Vérifier si le format est supporté
    if not image_processor.is_supported(filename):
        logger.warning(f"Format non supporté pour conversion: {filename}")
        return
    
    try:
        # Convertir en WebP
        webp_content = image_processor.convert_to_webp(image_field.file)
        
        if webp_content:
            # Remplacer l'image originale par la version WebP
            setattr(instance, field_name, webp_content)
            logger.info(f"Image convertie en WebP: {filename} -> {webp_content.name}")
        else:
            logger.warning(f"Échec conversion WebP pour: {filename}")
            
    except Exception as e:
        logger.error(f"Erreur lors de la conversion WebP: {e}")


@receiver(pre_save, sender=Project)
def convert_project_thumbnail_to_webp(sender, instance, **kwargs):
    """Convertit automatiquement le thumbnail du projet en WebP."""
    if instance.pk:
        # Récupérer l'ancienne valeur pour comparer
        try:
            old_instance = Project.objects.get(pk=instance.pk)
            if old_instance.thumbnail == instance.thumbnail:
                return  # Pas de changement
        except Project.DoesNotExist:
            pass
    
    convert_image_to_webp(instance, 'thumbnail')


@receiver(pre_save, sender=ProjectImage)
def convert_project_image_to_webp(sender, instance, **kwargs):
    """Convertit automatiquement les images de projet en WebP."""
    if instance.pk:
        try:
            old_instance = ProjectImage.objects.get(pk=instance.pk)
            if old_instance.image == instance.image:
                return
        except ProjectImage.DoesNotExist:
            pass
    
    convert_image_to_webp(instance, 'image')
