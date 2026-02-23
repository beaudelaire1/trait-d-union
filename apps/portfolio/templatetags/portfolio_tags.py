"""Template filters for the portfolio app."""
from __future__ import annotations

import re

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
    "hr",
]
ALLOWED_ATTRIBUTES = {
    "a": ["href", "title"],
}


def _normalize_text(value: str) -> str:
    """Pre-process user text so it converts cleanly to Markdown.

    Fixes common issues:
    - ``-item`` → ``- item`` (missing space after dash for lists)
    - Single newlines between paragraphs → double newlines
    - Ensures blank line before list items so Markdown parses them
    """
    lines = value.replace('\r\n', '\n').replace('\r', '\n').split('\n')
    result: list[str] = []

    for line in lines:
        stripped = line.strip()

        # Fix: -item or - item (ensure "- " prefix for list items)
        # Matches lines starting with - followed by a non-space, non-dash char
        if re.match(r'^-([^\s\-])', stripped):
            stripped = '- ' + stripped[1:]

        result.append(stripped)

    # Rejoin and ensure blank lines before list blocks and headings
    text = '\n'.join(result)

    # Ensure blank line before a list item if previous line is not blank or list
    text = re.sub(r'([^\n])\n(- )', r'\1\n\n\2', text)

    # Ensure blank line before headings (### ...)
    text = re.sub(r'([^\n])\n(#{1,5} )', r'\1\n\n\2', text)

    # Ensure blank line before **Bold title** at start of line (treat as paragraph)
    text = re.sub(r'([^\n])\n(\*\*[^*]+\*\*)', r'\1\n\n\2', text)

    # Convert single newlines between non-empty lines to double (paragraph breaks)
    # But preserve existing double newlines and list continuations
    text = re.sub(r'(?<!\n)\n(?!\n)(?!- )(?!\d+\. )(?!#)(?!\*\*)', '\n\n', text)

    return text


@register.filter(name="md")
def markdown_filter(value: str) -> str:
    """Convert a Markdown string to safe HTML.

    Usage: {{ project.objective|md }}

    Pre-processes text to fix common formatting issues, then converts
    Markdown to HTML. Only a strict whitelist of HTML tags is kept (via bleach).
    """
    if not value:
        return ""

    # Normalize user input
    normalized = _normalize_text(value)

    # Convert Markdown → raw HTML
    html = md.markdown(
        normalized,
        extensions=["smarty"],  # smart quotes only
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
