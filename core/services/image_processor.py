"""
Service de traitement d'images optimisé.

Fonctionnalités :
- Conversion automatique en WebP (meilleur support) et AVIF (meilleure compression)
- Redimensionnement intelligent
- Génération de thumbnails
- Lazy loading attributes automatiques

Usage :
    from core.services.image_processor import ImageProcessor
    
    processor = ImageProcessor()
    webp_path = processor.convert_to_webp(image_file)
    thumbnail = processor.create_thumbnail(image_file, size=(400, 300))
"""
from __future__ import annotations

import io
import logging
from pathlib import Path
from typing import Optional, Tuple

from django.core.files.base import ContentFile
from django.core.files.uploadedfile import InMemoryUploadedFile

logger = logging.getLogger(__name__)

# Formats supportés
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'}
WEBP_QUALITY = 85
AVIF_QUALITY = 80
MAX_DIMENSION = 2000  # Pixels


class ImageProcessor:
    """Processeur d'images avec conversion et optimisation."""
    
    def __init__(self, quality_webp: int = WEBP_QUALITY, quality_avif: int = AVIF_QUALITY):
        self.quality_webp = quality_webp
        self.quality_avif = quality_avif
        self._pillow_available = None
    
    @property
    def pillow_available(self) -> bool:
        """Vérifie si Pillow est disponible avec le support WebP/AVIF."""
        if self._pillow_available is None:
            try:
                from PIL import Image, features
                self._pillow_available = True
                # Vérifier le support AVIF (optionnel)
                self._avif_support = features.check('avif')
                self._webp_support = features.check('webp')
            except ImportError:
                self._pillow_available = False
                self._avif_support = False
                self._webp_support = False
        return self._pillow_available
    
    def is_supported(self, filename: str) -> bool:
        """Vérifie si le format d'image est supporté."""
        ext = Path(filename).suffix.lower()
        return ext in SUPPORTED_FORMATS
    
    def convert_to_webp(
        self,
        image_file,
        quality: Optional[int] = None,
        max_size: Optional[Tuple[int, int]] = None,
    ) -> Optional[ContentFile]:
        """
        Convertit une image en WebP.
        
        Args:
            image_file: Fichier image Django (InMemoryUploadedFile ou FieldFile)
            quality: Qualité de compression (0-100)
            max_size: Dimensions maximales (width, height)
        
        Returns:
            ContentFile avec l'image WebP, ou None si échec
        """
        if not self.pillow_available or not self._webp_support:
            logger.warning("WebP non supporté par cette installation de Pillow")
            return None
        
        try:
            from PIL import Image
            
            # Ouvrir l'image
            image_file.seek(0)
            img = Image.open(image_file)
            
            # Convertir en RGB si nécessaire (WebP ne supporte pas tous les modes)
            if img.mode in ('RGBA', 'LA', 'P'):
                # Garder la transparence
                if img.mode == 'P':
                    img = img.convert('RGBA')
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Redimensionner si nécessaire
            if max_size:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            elif max(img.size) > MAX_DIMENSION:
                img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.Resampling.LANCZOS)
            
            # Convertir en WebP
            output = io.BytesIO()
            img.save(
                output,
                format='WEBP',
                quality=quality or self.quality_webp,
                method=6,  # Meilleure compression (plus lent)
            )
            output.seek(0)
            
            # Générer le nom de fichier
            original_name = getattr(image_file, 'name', 'image')
            new_name = Path(original_name).stem + '.webp'
            
            logger.info(f"Image convertie en WebP: {original_name} -> {new_name}")
            return ContentFile(output.read(), name=new_name)
            
        except Exception as e:
            logger.error(f"Erreur conversion WebP: {e}")
            return None
    
    def convert_to_avif(
        self,
        image_file,
        quality: Optional[int] = None,
        max_size: Optional[Tuple[int, int]] = None,
    ) -> Optional[ContentFile]:
        """
        Convertit une image en AVIF (meilleure compression, support limité).
        
        Args:
            image_file: Fichier image Django
            quality: Qualité de compression (0-100)
            max_size: Dimensions maximales
        
        Returns:
            ContentFile avec l'image AVIF, ou None si non supporté
        """
        if not self.pillow_available or not self._avif_support:
            logger.debug("AVIF non supporté, fallback WebP recommandé")
            return None
        
        try:
            from PIL import Image
            
            image_file.seek(0)
            img = Image.open(image_file)
            
            # AVIF supporte RGB et RGBA
            if img.mode not in ('RGB', 'RGBA'):
                img = img.convert('RGB')
            
            # Redimensionner
            if max_size:
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
            elif max(img.size) > MAX_DIMENSION:
                img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.Resampling.LANCZOS)
            
            output = io.BytesIO()
            img.save(
                output,
                format='AVIF',
                quality=quality or self.quality_avif,
            )
            output.seek(0)
            
            original_name = getattr(image_file, 'name', 'image')
            new_name = Path(original_name).stem + '.avif'
            
            logger.info(f"Image convertie en AVIF: {original_name} -> {new_name}")
            return ContentFile(output.read(), name=new_name)
            
        except Exception as e:
            logger.error(f"Erreur conversion AVIF: {e}")
            return None
    
    def create_thumbnail(
        self,
        image_file,
        size: Tuple[int, int] = (400, 300),
        format: str = 'webp',
    ) -> Optional[ContentFile]:
        """
        Crée un thumbnail optimisé.
        
        Args:
            image_file: Fichier image source
            size: Dimensions du thumbnail (width, height)
            format: Format de sortie ('webp', 'avif', 'jpeg')
        
        Returns:
            ContentFile avec le thumbnail
        """
        if not self.pillow_available:
            return None
        
        try:
            from PIL import Image
            
            image_file.seek(0)
            img = Image.open(image_file)
            
            # Thumbnail avec crop centré pour respecter le ratio exact
            img_ratio = img.width / img.height
            target_ratio = size[0] / size[1]
            
            if img_ratio > target_ratio:
                # Image plus large : crop horizontal
                new_width = int(img.height * target_ratio)
                left = (img.width - new_width) // 2
                img = img.crop((left, 0, left + new_width, img.height))
            else:
                # Image plus haute : crop vertical
                new_height = int(img.width / target_ratio)
                top = (img.height - new_height) // 2
                img = img.crop((0, top, img.width, top + new_height))
            
            # Redimensionner
            img = img.resize(size, Image.Resampling.LANCZOS)
            
            # Convertir en RGB si nécessaire
            if format.lower() in ('jpeg', 'jpg') and img.mode in ('RGBA', 'LA', 'P'):
                img = img.convert('RGB')
            elif img.mode == 'P':
                img = img.convert('RGBA')
            
            output = io.BytesIO()
            
            if format.lower() == 'webp' and self._webp_support:
                img.save(output, format='WEBP', quality=self.quality_webp)
                ext = '.webp'
            elif format.lower() == 'avif' and self._avif_support:
                img.save(output, format='AVIF', quality=self.quality_avif)
                ext = '.avif'
            else:
                img.save(output, format='JPEG', quality=85)
                ext = '.jpg'
            
            output.seek(0)
            original_name = getattr(image_file, 'name', 'image')
            new_name = f"{Path(original_name).stem}_thumb{ext}"
            
            return ContentFile(output.read(), name=new_name)
            
        except Exception as e:
            logger.error(f"Erreur création thumbnail: {e}")
            return None
    
    def optimize_for_web(
        self,
        image_file,
        max_width: int = 1920,
        generate_webp: bool = True,
        generate_avif: bool = False,
    ) -> dict:
        """
        Optimise une image pour le web avec plusieurs formats.
        
        Args:
            image_file: Image source
            max_width: Largeur maximale
            generate_webp: Générer version WebP
            generate_avif: Générer version AVIF
        
        Returns:
            Dict avec les fichiers générés: {'original': ..., 'webp': ..., 'avif': ...}
        """
        result = {'original': image_file, 'webp': None, 'avif': None}
        
        if generate_webp:
            result['webp'] = self.convert_to_webp(
                image_file,
                max_size=(max_width, max_width)
            )
        
        if generate_avif:
            result['avif'] = self.convert_to_avif(
                image_file,
                max_size=(max_width, max_width)
            )
        
        return result


# Singleton pour import facile
image_processor = ImageProcessor()


def process_uploaded_image(image_file, create_webp: bool = True) -> dict:
    """
    Fonction utilitaire pour traiter une image uploadée.
    
    Usage dans un modèle Django:
        def save(self, *args, **kwargs):
            if self.image:
                from core.services.image_processor import process_uploaded_image
                result = process_uploaded_image(self.image)
                if result.get('webp'):
                    self.image_webp = result['webp']
            super().save(*args, **kwargs)
    """
    return image_processor.optimize_for_web(
        image_file,
        generate_webp=create_webp,
        generate_avif=False,  # AVIF pas encore assez supporté
    )
