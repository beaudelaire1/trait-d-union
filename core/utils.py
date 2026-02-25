"""Utilitaires partagés pour le projet Trait d'Union Studio."""
from decimal import Decimal


def num2words_fr(value: Decimal) -> str:
    """Convertit un montant décimal en toutes lettres (français).

    Utilise ``num2words`` si disponible, sinon retourne la valeur
    formatée en français (virgule comme séparateur décimal).
    """
    try:
        from num2words import num2words
        return num2words(value, lang='fr')
    except ImportError:
        return str(value).replace(".", ",")
