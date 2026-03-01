"""Custom template filters for chroniques app with XSS protection."""
import nh3
from django import template
from django.utils.safestring import mark_safe

register = template.Library()

# Whitelist HTML tags and attributes for article content
ALLOWED_TAGS = {
    'p', 'br', 'strong', 'b', 'em', 'i', 'u',
    'ul', 'ol', 'li',
    'a', 'h3', 'h4', 'h5', 'h6',
    'blockquote', 'code', 'pre', 'hr',
    'img', 'figure', 'figcaption',
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
}

ALLOWED_ATTRIBUTES = {
    'a': {'href', 'title', 'target', 'rel'},
    'img': {'src', 'alt', 'title', 'width', 'height', 'loading'},
    'code': {'class'},
    'pre': {'class'},
    '*': {'class', 'id'},
}


@register.filter(name='safe_html')
def safe_html(value):
    """Sanitize HTML content to prevent XSS attacks.
    
    Uses nh3 library to clean HTML while preserving safe tags and attributes.
    This filter should be used instead of |safe for user-generated content.
    
    Usage:
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
    return mark_safe(clean)
