"""Template filters for the portfolio app."""
from __future__ import annotations

import bleach
import markdown as md
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
    "code",
]
ALLOWED_ATTRIBUTES = {
    "a": ["href", "title"],
}


@register.filter(name="md")
def markdown_filter(value: str) -> str:
    """Convert a Markdown string to safe HTML.

    Usage: {{ project.objective|md }}

    Only a strict whitelist of HTML tags is kept (via bleach).
    """
    if not value:
        return ""
    # Convert Markdown → raw HTML
    html = md.markdown(
        value,
        extensions=["nl2br", "smarty"],  # nl2br = newlines → <br>, smarty = smart quotes
        output_format="html",
    )
    # Sanitize – keep only whitelisted tags
    clean = bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        strip=True,
    )
    return mark_safe(clean)
