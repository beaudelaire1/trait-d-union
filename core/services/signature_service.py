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
from datetime import UTC
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

    MIN_WIDTH = 100
    MIN_HEIGHT = 50
    MAX_BASE64_SIZE = 500 * 1024

    @classmethod
    def validate_signature_data(cls, base64_data: str) -> Tuple[bool, str]:
        if not base64_data:
            return False, "Aucune signature fournie"

        if len(base64_data) > cls.MAX_BASE64_SIZE:
            return False, "La signature est trop volumineuse"

        if base64_data.startswith('data:image'):
            try:
                base64_data = base64_data.split(',')[1]
            except IndexError:
                return False, "Format de signature invalide"

        try:
            image_data = base64.b64decode(base64_data)
        except Exception:
            return False, "Données base64 invalides"

        if PIL_AVAILABLE:
            try:
                img = Image.open(BytesIO(image_data))
                if img.format not in ('PNG', 'JPEG'):
                    return False, "Format d'image non supporté (PNG requis)"
                if img.width < cls.MIN_WIDTH or img.height < cls.MIN_HEIGHT:
                    return False, f"Signature trop petite (min {cls.MIN_WIDTH}x{cls.MIN_HEIGHT}px)"
                if cls._is_blank_image(img):
                    return False, "La signature semble vide"
            except Exception as e:
                logger.error(f"Erreur validation image: {e}")
                return False, "Image corrompue ou invalide"

        return True, "Signature valide"

    @classmethod
    def _is_blank_image(cls, img: "Image.Image") -> bool:
        if not PIL_AVAILABLE:
            return False

        try:
            if img.mode != 'RGBA':
                img = img.convert('RGBA')

            if hasattr(img, 'get_flattened_data'):
                pixels = img.get_flattened_data()
            else:
                pixels = tuple(img.getdata())

            non_blank = 0
            for r, g, b, a in pixels:
                if a > 10 and (r < 250 or g < 250 or b < 250):
                    non_blank += 1

            threshold = len(pixels) * 0.01
            return non_blank < threshold

        except Exception:
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
        now = timezone.now()

        audit_trail = {
            'version': '1.0',
            'timestamp': now.isoformat(),
            'timestamp_utc': now.astimezone(UTC).isoformat().replace('+00:00', 'Z'),
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
        if base64_data.startswith('data:image'):
            base64_data = base64_data.split(',')[1]

        if not base64_data or not base64_data.strip():
            return None

        try:
            image_data = base64.b64decode(base64_data, validate=True)
        except Exception:
            return None

        if not image_data:
            return None

        save_dir = os.path.join(settings.MEDIA_ROOT, subdir)
        os.makedirs(save_dir, exist_ok=True)

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
        if base64_data.startswith('data:image'):
            base64_data = base64_data.split(',')[1]

        return hashlib.sha256(base64_data.encode()).hexdigest()

    @classmethod
    def get_client_ip(cls, request) -> str:
        from core.utils import get_client_ip
        return get_client_ip(request)
