"""Utilitaires pour l'application `factures`.

WARNING: DEPRECATED - This module is kept for backward compatibility.
All utilities are now centralized in `core.utils`.
"""
from core.utils import num2words_fr  # noqa: F401 -- re-export for compatibility

__all__ = ['num2words_fr']
