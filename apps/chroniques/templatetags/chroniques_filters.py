"""Custom template filters for chroniques app with XSS protection."""
import re

import nh3
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

# ---------------------------------------------------------------------------
# Whitelist HTML tags and attributes for article content
# ---------------------------------------------------------------------------
ALLOWED_TAGS = {
    'p', 'br', 'strong', 'b', 'em', 'i', 'u', 'sub', 'sup', 'span', 'div',
    'ul', 'ol', 'li',
    'a', 'h2', 'h3', 'h4', 'h5', 'h6',
    'blockquote', 'code', 'pre', 'hr',
    'img', 'figure', 'figcaption',
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
}

# `style` is allowed per-tag so nh3 preserves it; a post-processor below
# strips any CSS property that is not in the safe-list.
ALLOWED_ATTRIBUTES = {
    'a': {'href', 'title', 'target'},  # 'rel' is set via link_rel param
    'img': {'src', 'alt', 'title', 'width', 'height', 'loading', 'style'},
    'p': {'style'},
    'h2': {'style'},
    'h3': {'style'},
    'h4': {'style'},
    'h5': {'style'},
    'h6': {'style'},
    'blockquote': {'style'},
    'div': {'style'},
    'span': {'style'},
    'td': {'colspan', 'rowspan', 'style'},
    'th': {'colspan', 'rowspan', 'style'},
    'code': {'class'},
    'pre': {'class'},
    '*': {'class', 'id'},
}

# ---------------------------------------------------------------------------
# CSS property sanitiser – only these properties survive in style="…"
# ---------------------------------------------------------------------------
_SAFE_CSS_PROP_RE = re.compile(
    r'(text-align|color|background-color|padding-left|padding-right'
    r'|margin-left|margin-right|text-indent)'
    r'\s*:\s*'
    r'([^;"<>()]+)',
    re.IGNORECASE,
)

_STYLE_ATTR_RE = re.compile(r'(style\s*=\s*")([^"]*?)(")', re.IGNORECASE)

_DANGEROUS_VALUES = ('url(', 'expression(', 'javascript:', 'import', 'behavior:')


def _sanitize_style_attr(match):
    """Keep only safe CSS properties inside a style attribute."""
    prefix, css_content, suffix = match.group(1), match.group(2), match.group(3)
    safe_props = []
    for prop_match in _SAFE_CSS_PROP_RE.finditer(css_content):
        prop_name = prop_match.group(1).strip().lower()
        prop_value = prop_match.group(2).strip()
        if any(bad in prop_value.lower() for bad in _DANGEROUS_VALUES):
            continue
        safe_props.append(f'{prop_name}: {prop_value}')
    if safe_props:
        return f'{prefix}{"; ".join(safe_props)}{suffix}'
    return ''  # drop empty/dangerous style attribute entirely


@register.filter(name='safe_html')
def safe_html(value):
    """Sanitize HTML content to prevent XSS while preserving formatting.

    1. nh3 strips dangerous tags / attributes (XSS protection).
    2. A post-processor keeps only safe CSS properties inside ``style``
       attributes (text-align, color, background-color …).

    Usage::

        {{ article.body|safe_html }}
    """
    if not value:
        return ''

    clean = nh3.clean(
        value,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        link_rel='noopener noreferrer',
    )
    # Post-process: only keep safe CSS properties
    clean = _STYLE_ATTR_RE.sub(_sanitize_style_attr, clean)
    return mark_safe(clean)
