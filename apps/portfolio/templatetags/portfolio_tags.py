"""Template filters for the portfolio app."""
from __future__ import annotations

import html as html_module

import nh3
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

# Tags HTML autorisés en sortie (whitelist stricte)
ALLOWED_TAGS = {
    "p", "br",
    "strong", "b", "em", "i", "u",
    "ul", "ol", "li",
    "h3", "h4", "h5",
    "blockquote",
    "a",
    "code", "hr",
}
ALLOWED_ATTRIBUTES = {
    "a": {"href", "title", "target"},
}


@register.filter(name="safe_html")
def safe_html_filter(value: str) -> str:
    """Sanitize HTML from TinyMCE — keep only whitelisted tags.

    Usage: {{ project.objective|safe_html }}
    """
    if not value:
        return ""
    clean = nh3.clean(
        value,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
    )
    return mark_safe(clean)


@register.filter(name="plain_text")
def plain_text_filter(value: str) -> str:
    """Strip ALL HTML tags and decode entities → plain unicode text.

    Usage: {{ project.objective|plain_text|truncatewords:20 }}
    Idéal pour les meta descriptions, alt text, et aperçus de cards.
    """
    if not value:
        return ""
    # 1. Strip all tags (nh3 with empty tag set)
    stripped = nh3.clean(value, tags=set())
    # 2. Decode HTML entities (&eacute; → é, &amp; → &, etc.)
    return html_module.unescape(stripped)


# Keep backward-compat alias for any template still using |md
@register.filter(name="md")
def markdown_filter(value: str) -> str:
    """Backward-compatible alias — just sanitizes HTML now."""
    return safe_html_filter(value)


# ── Audit Ch.05 — score 0-100 → grade lettre (A+/A/A-/B+/B/C/D/F) ────
@register.filter(name="score_grade")
def score_grade(value) -> str:
    """Convertit un score 0-100 en grade lettre type SSL Labs.

    Usage : {{ score|score_grade }}  →  "A+", "A", "B+", "C", ...
    Échelle alignée sur les conventions courantes (PageSpeed ≥90 = A+).
    """
    try:
        s = int(value)
    except (TypeError, ValueError):
        return ""
    if s >= 95:
        return "A+"
    if s >= 90:
        return "A"
    if s >= 85:
        return "A-"
    if s >= 80:
        return "B+"
    if s >= 70:
        return "B"
    if s >= 60:
        return "C"
    if s >= 50:
        return "D"
    return "F"


@register.filter(name="grade_label")
def grade_label(grade: str) -> str:
    """Renvoie un libellé qualitatif à partir d'un grade lettre."""
    if not grade:
        return ""
    g = grade.upper().strip()
    return {
        "A+": "Excellent",
        "A": "Très bon",
        "A-": "Très bon",
        "B+": "Bon",
        "B": "Bon",
        "C": "Moyen",
        "D": "À améliorer",
        "F": "Critique",
    }.get(g, "")
