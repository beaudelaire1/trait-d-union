"""
Signature Service — Service de signature électronique

Ce module gère :
- Validation des signatures (format base64 PNG)
- Génération d'audit trail (IP, Date, UserAgent)
- Intégration avec les PDFs de devis

La signature côté client utilise signature_pad.js
"""

import os
import base64
import hashlib
import json
import logging
from datetime import datetime
from io import BytesIO
from typing import Optional, Dict, Any, Tuple

from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

# Import conditionnel de PIL
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    Image = None
    PIL_AVAILABLE = False
    logger.warning("Pillow non installé. Validation des signatures désactivée.")


class SignatureService:
    """Service de gestion des signatures électroniques."""

    # Dimensions minimales pour une signature valide
    MIN_WIDTH = 100
    MIN_HEIGHT = 50

    # Taille maximale du fichier base64 (500KB)
    MAX_BASE64_SIZE = 500 * 1024

    @classmethod
    def validate_signature_data(cls, base64_data: str) -> Tuple[bool, str]:
        """
        Valide les données de signature base64.

        Args:
            base64_data: Image PNG en base64 (avec ou sans préfixe data:image)

        Returns:
            Tuple (is_valid, message)
        """
        if not base64_data:
            return False, "Aucune signature fournie"

        # Vérifier la taille
        if len(base64_data) > cls.MAX_BASE64_SIZE:
            return False, "La signature est trop volumineuse"

        # Nettoyer le préfixe data:image/png;base64,
        if base64_data.startswith('data:image'):
            try:
                base64_data = base64_data.split(',')[1]
            except IndexError:
                return False, "Format de signature invalide"

        # Décoder le base64
        try:
            image_data = base64.b64decode(base64_data)
        except Exception:
            return False, "Données base64 invalides"

        # Valider avec PIL si disponible
        if PIL_AVAILABLE:
            try:
                img = Image.open(BytesIO(image_data))

                # Vérifier le format
                if img.format not in ('PNG', 'JPEG'):
                    return False, "Format d'image non supporté (PNG requis)"

                # Vérifier les dimensions minimales
                if img.width < cls.MIN_WIDTH or img.height < cls.MIN_HEIGHT:
                    return False, f"Signature trop petite (min {cls.MIN_WIDTH}x{cls.MIN_HEIGHT}px)"

                # Vérifier que l'image n'est pas vide (tout blanc/transparent)
                if cls._is_blank_image(img):
                    return False, "La signature semble vide"

            except Exception as e:
                logger.error(f"Erreur validation image: {e}")
                return False, "Image corrompue ou invalide"

        return True, "Signature valide"

    @classmethod
    def _is_blank_image(cls, img: "Image.Image") -> bool:
        """
        Vérifie si une image est vide (tout blanc ou transparent).

        Returns:
            True si l'image est considérée comme vide
        """
        if not PIL_AVAILABLE:
            return False

        try:
            # Convertir en RGBA pour avoir accès à la transparence
            if img.mode != 'RGBA':
                img = img.convert('RGBA')

            # Compter les pixels non-blancs et non-transparents
            pixels = list(img.getdata())
            non_blank = 0
            for r, g, b, a in pixels:
                # Pixel visible (non transparent) et non blanc
                if a > 10 and (r < 250 or g < 250 or b < 250):
                    non_blank += 1

            # Si moins de 1% des pixels sont "dessinés", considérer comme vide
            threshold = len(pixels) * 0.01
            return non_blank < threshold

        except Exception:
            # En cas d'erreur, ne pas bloquer
            return False

    @classmethod
    def generate_audit_trail(
        cls,
        client_ip: str,
        user_agent: str,
        document_type: str,
        document_id: str,
        document_number: str,
        signer_name: str,
        signer_email: str,
        signature_hash: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Génère un audit trail pour une signature.

        Args:
            client_ip: Adresse IP du signataire
            user_agent: User-Agent du navigateur
            document_type: Type de document (quote, invoice)
            document_id: ID du document
            document_number: Numéro du document
            signer_name: Nom du signataire
            signer_email: Email du signataire
            signature_hash: Hash SHA256 de la signature (optionnel)

        Returns:
            Dict contenant toutes les informations d'audit
        """
        now = timezone.now()

        audit_trail = {
            'version': '1.0',
            'timestamp': now.isoformat(),
            'timestamp_utc': now.utcnow().isoformat() + 'Z',
            'timezone': str(settings.TIME_ZONE),

            'document': {
                'type': document_type,
                'id': document_id,
                'number': document_number,
            },

            'signer': {
                'name': signer_name,
                'email': signer_email,
            },

            'technical': {
                'ip_address': client_ip,
                'user_agent': user_agent,
                'signature_hash': signature_hash,
            },

            'legal': {
                'statement': (
                    f"Je soussigné(e) {signer_name} ({signer_email}) "
                    f"certifie avoir pris connaissance du document {document_number} "
                    f"et accepte les termes et conditions qui y sont décrits."
                ),
                'acceptance_method': 'electronic_signature',
                'platform': "Trait d'Union Studio",
            },
        }

        # Calculer le hash de l'audit trail lui-même
        audit_string = json.dumps(audit_trail, sort_keys=True, ensure_ascii=False)
        audit_trail['integrity_hash'] = hashlib.sha256(audit_string.encode()).hexdigest()

        return audit_trail

    @classmethod
    def save_signature_image(
        cls,
        base64_data: str,
        filename: str,
        subdir: str = "signatures"
    ) -> Optional[str]:
        """
        Sauvegarde une image de signature sur le système de fichiers.

        Args:
            base64_data: Image en base64
            filename: Nom du fichier (sans extension)
            subdir: Sous-répertoire dans MEDIA_ROOT

        Returns:
            Chemin relatif du fichier sauvegardé ou None si erreur
        """
        # Nettoyer le préfixe
        if base64_data.startswith('data:image'):
            base64_data = base64_data.split(',')[1]

        try:
            image_data = base64.b64decode(base64_data)
        except Exception:
            return None

        # Créer le répertoire si nécessaire
        save_dir = os.path.join(settings.MEDIA_ROOT, subdir)
        os.makedirs(save_dir, exist_ok=True)

        # Sauvegarder le fichier
        filepath = os.path.join(save_dir, f"{filename}.png")
        relative_path = os.path.join(subdir, f"{filename}.png")

        try:
            with open(filepath, 'wb') as f:
                f.write(image_data)
            logger.info(f"Signature sauvegardée: {relative_path}")
            return relative_path
        except Exception as e:
            logger.error(f"Erreur sauvegarde signature: {e}")
            return None

    @classmethod
    def compute_signature_hash(cls, base64_data: str) -> str:
        """
        Calcule le hash SHA256 d'une signature.

        Args:
            base64_data: Image en base64

        Returns:
            Hash SHA256 en hexadécimal
        """
        # Nettoyer le préfixe
        if base64_data.startswith('data:image'):
            base64_data = base64_data.split(',')[1]

        return hashlib.sha256(base64_data.encode()).hexdigest()

    @classmethod
    def get_client_ip(cls, request) -> str:
        """
        Récupère l'adresse IP réelle du client.

        Gère les proxies (X-Forwarded-For) et Render.
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            # Prendre la première IP (client original)
            ip = x_forwarded_for.split(',')[0].strip()
        else:
            ip = request.META.get('REMOTE_ADDR', 'unknown')
        return ip
