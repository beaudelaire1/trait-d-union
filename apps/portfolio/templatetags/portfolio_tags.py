"""Template filters for the portfolio app."""
from __future__ import annotations

import html as html_module

import bleach
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

# Tags HTML autorisés en sortie (whitelist stricte)
ALLOWED_TAGS = [
    "p", "br",
    "strong", "b", "em", "i", "u",
    "ul", "ol", "li",
    "h3", "h4", "h5",
    "blockquote",
    "a",
    "code", "hr",
]
ALLOWED_ATTRIBUTES = {
    "a": ["href", "title", "target"],
}


@register.filter(name="safe_html")
def safe_html_filter(value: str) -> str:
    """Sanitize HTML from TinyMCE — keep only whitelisted tags.

    Usage: {{ project.objective|safe_html }}
    """
    if not value:
        return ""
    clean = bleach.clean(
        value,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True,
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
    # 1. Strip all tags (bleach with empty tag list)
    stripped = bleach.clean(value, tags=[], strip=True)
    # 2. Decode HTML entities (&eacute; → é, &amp; → &, etc.)
    return html_module.unescape(stripped)


# Keep backward-compat alias for any template still using |md
@register.filter(name="md")
def markdown_filter(value: str) -> str:
    """Backward-compatible alias — just sanitizes HTML now."""
    return safe_html_filter(value)
