"""Modèles transversaux (contexte/forms/services).

Note : AuditLog et StripeEventLog vivent dans apps.audit.models.
Re-export ici pour compatibilité d'import.
"""

from apps.audit.models import StripeEventLog  # noqa: F401
