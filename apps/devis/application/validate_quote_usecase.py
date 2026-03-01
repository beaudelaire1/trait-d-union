"""Use cases pour la validation des devis et onboarding client.

Architecture :
- ValidateQuoteUseCase : valider un devis (SENT → VALIDATED), enregistrer audit
- ProvisionClientAccountUseCase : créer/activer compte client post-validation
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Dict, Any

from django.db import transaction, IntegrityError
from django.contrib.auth.models import User
from django.utils import timezone
from django.core.exceptions import ValidationError

from apps.devis.models import Quote
from apps.clients.models import ClientProfile
from apps.audit.models import AuditLog
from core.utils import get_client_ip

logger = logging.getLogger(__name__)


class QuoteValidationError(Exception):
    """Erreur lors de la validation d'un devis."""


class ClientAccountProvisionError(Exception):
    """Erreur lors de la création du compte client."""


@dataclass(frozen=True)
class ValidateQuoteResult:
    """Résultat de ValidateQuoteUseCase."""
    quote: Quote
    validated_by: User
    validated_at: datetime
    audit_trail: Dict[str, Any]


@dataclass(frozen=True)
class ProvisionClientResult:
    """Résultat de ProvisionClientAccountUseCase."""
    user: User
    client_profile: ClientProfile
    is_new: bool
    temporary_password: Optional[str]


def validate_quote(
    quote: Quote,
    validated_by: User,
    *,
    request=None,
    comment: str = "",
) -> ValidateQuoteResult:
    """Use case : valider un devis (SENT → VALIDATED).
    
    Effets :
    - Quote.status = VALIDATED
    - Quote.validated_by = utilisateur
    - Quote.validated_at = now
    - Quote.validated_audit_trail = métadonnées {ip, user_agent, comment, timestamp}
    - Log audit centralisé
    - Signal pour onboarding client (voir signals.py)
    
    Args:
        quote: Quote à valider
        validated_by: User qui valide
        request: HttpRequest (optionnel, pour IP/user-agent)
        comment: Commentaire optionnel
    
    Returns:
        ValidateQuoteResult avec audit trail
    
    Raises:
        QuoteValidationError si devis pas au bon statut
    """
    if quote.status != Quote.QuoteStatus.SENT:
        raise QuoteValidationError(
            f"Devis {quote.number} non validable (statut={quote.status}). "
            f"Doit être au statut SENT."
        )
    
    # Préparation audit trail
    audit_data = {
        'timestamp': timezone.now().isoformat(),
        'validated_by_id': validated_by.pk,
        'validated_by_username': validated_by.username,
        'comment': comment or "",
    }
    
    if request:
        audit_data['ip'] = get_client_ip(request)
        audit_data['user_agent'] = request.META.get('HTTP_USER_AGENT', '')[:500]
    
    # Transaction atomique
    with transaction.atomic():
        quote.status = Quote.QuoteStatus.VALIDATED
        quote.validated_by = validated_by
        quote.validated_at = timezone.now()
        quote.validated_audit_trail = audit_data
        quote.save(update_fields=[
            'status',
            'validated_by',
            'validated_at',
            'validated_audit_trail'
        ])
        
        # Log audit centralisé
        AuditLog.log_action(
            action_type=AuditLog.ActionType.QUOTE_VALIDATED,
            actor=validated_by,
            content_type='devis.Quote',
            object_id=quote.pk,
            description=f"Devis {quote.number} validé par {validated_by.username}",
            metadata={
                'quote_id': quote.pk,
                'quote_number': quote.number,
                'quote_total_ttc': str(quote.total_ttc),
                'client_id': quote.client.pk if quote.client else None,
                'client_email': quote.client.email if quote.client else None,
                'comment': comment,
                **audit_data,
            }
        )
    
    logger.info(
        f"Devis validé: {quote.number} par {validated_by.username}",
        extra={'quote_pk': quote.pk}
    )
    
    return ValidateQuoteResult(
        quote=quote,
        validated_by=validated_by,
        validated_at=quote.validated_at,
        audit_trail=audit_data,
    )


def provision_client_account(
    quote: Quote,
    *,
    request=None,
) -> ProvisionClientResult:
    """Use case : créer/activer un compte client après validation du devis.
    
    Délègue la création du compte au service centralisé
    ``apps.clients.services.create_client_account``.
    
    Args:
        quote: Quote validée
        request: HttpRequest (optionnel)
    
    Returns:
        ProvisionClientResult
    
    Raises:
        ClientAccountProvisionError si erreur critique
    """
    from apps.clients.services import create_client_account, ClientAccountError

    if not quote.client_id:
        raise ClientAccountProvisionError(
            f"Quote {quote.number} n'a pas de client associé."
        )
    
    client_email = quote.client.email
    if not client_email:
        raise ClientAccountProvisionError(
            f"Client du devis {quote.number} sans email."
        )
    
    try:
        result = create_client_account(
            email=client_email,
            full_name=quote.client.full_name or '',
            company_name=quote.client.company or '',
            phone=quote.client.phone or '',
            address=quote.client.address_line or '',
            send_email=True,
        )
    except ClientAccountError as e:
        raise ClientAccountProvisionError(str(e))
    
    # Log audit si nouveau compte
    if result.is_new:
        AuditLog.log_action(
            action_type=AuditLog.ActionType.CLIENT_ACCOUNT_CREATED,
            actor=None,  # Action système
            content_type='auth.User',
            object_id=result.user.pk,
            description=f"Compte client créé pour {client_email} (devis {quote.number})",
            metadata={
                'user_id': result.user.pk,
                'email': client_email,
                'quote_id': quote.pk,
                'quote_number': quote.number,
                'temporary_password_set': True,
            }
        )
    
    # 🛡️ SECURITY: Ensure the quote's Client record is linked to the profile
    if quote.client and not quote.client.linked_profile_id:
        quote.client.linked_profile = result.client_profile
        quote.client.save(update_fields=['linked_profile'])

    return ProvisionClientResult(
        user=result.user,
        client_profile=result.client_profile,
        is_new=result.is_new,
        temporary_password=result.temporary_password,
    )

