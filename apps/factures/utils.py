"""
Utilitaires pour l'application ``factures``.

Ce module fournit notamment ``num2words_fr`` qui convertit un montant
décimal en toutes lettres en français.  Il gère les nombres jusqu'à 999 999
et les centimes.  Pour un usage professionnel, il est recommandé
d'utiliser une bibliothèque dédiée telle que ``num2words``, mais cette
implémentation de base évite les dépendances externes.

    En 2025, les utilitaires ont été légèrement refactorisés pour gérer les
    montants négatifs (renvoyés avec un préfixe « moins ») et pour documenter
    explicitement l'origine des visuels du site (désormais stockés dans
    ``static/img``).  Toute référence à Unsplash a été supprimée.  Cette
    fonction reste néanmoins volontairement simple et sans recours à d'autres
    librairies【668280112401708†L16-L63】.
"""

from decimal import Decimal


UNITS = [
    "zéro",
    "un",
    "deux",
    "trois",
    "quatre",
    "cinq",
    "six",
    "sept",
    "huit",
    "neuf",
    "dix",
    "onze",
    "douze",
    "treize",
    "quatorze",
    "quinze",
    "seize",
]


def _convert_nn(n: int) -> str:
    """Convert a number < 100 to French words."""
    if n < 17:
        return UNITS[n]
    elif n < 20:
        return "dix-" + UNITS[n - 10]
    elif n < 70:
        tens = ["", "dix", "vingt", "trente", "quarante", "cinquante", "soixante"]
        t = tens[n // 10]
        u = n % 10
        if u == 0:
            return t
        elif u == 1 and (n < 60):
            return t + " et un"
        else:
            return t + "-" + UNITS[u]
    elif n < 80:
        # 70-79: soixante + 10-19
        return "soixante-" + _convert_nn(n - 60)
    elif n < 100:
        # 80-99: quatre-vingt + 0-19
        base = "quatre-vingt"
        if n == 80:
            return base + "s"
        return base + "-" + _convert_nn(n - 80)
    raise ValueError("Nombre hors limite")


def _convert_nnn(n: int) -> str:
    """Convert a number < 1000 to French words."""
    if n < 100:
        return _convert_nn(n)
    hundreds = n // 100
    remainder = n % 100
    if hundreds == 1:
        prefix = "cent"
    else:
        prefix = UNITS[hundreds] + " cent"
    if remainder == 0:
        if hundreds > 1:
            return prefix + "s"
        return prefix
    return prefix + " " + _convert_nn(remainder)


def num2words_fr(amount: Decimal) -> str:
    """
    Convertit un montant en toutes lettres en français.

    Exemple : ``1234.56`` -> ``"mille deux cent trente-quatre et cinquante-six centimes"``.

    :param amount: montant en euros à convertir.  Les montants négatifs sont
      précédés du mot « moins ».
    :return: représentation textuelle en français.
    """
    # Gère les montants négatifs en préfixant « moins »
    sign = ""
    if amount < 0:
        sign = "moins "
        amount = -amount

    # Sépare la partie entière et les centimes
    quantized = amount.quantize(Decimal("0.01"))
    integer_part = int(quantized)
    decimal_part = int((quantized - Decimal(integer_part)) * 100)

    words = []

    if integer_part == 0:
        words.append(UNITS[0])
    else:
        millions = integer_part // 1_000_000
        thousands = (integer_part % 1_000_000) // 1_000
        remainder = integer_part % 1_000

        if millions:
            if millions == 1:
                words.append("un million")
            else:
                words.append(_convert_nnn(millions) + " millions")
        if thousands:
            if thousands == 1:
                words.append("mille")
            else:
                words.append(_convert_nnn(thousands) + " mille")
        if remainder:
            words.append(_convert_nnn(remainder))

    result = " ".join(words)

    # Ajout des centimes
    if decimal_part > 0:
        result += " et " + _convert_nn(decimal_part) + " centimes"

    return sign + result