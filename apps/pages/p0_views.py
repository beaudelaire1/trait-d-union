"""Vues de stabilisation issues de l'audit P0 du 21 août 2026."""
from __future__ import annotations

import logging

from .views import HomeView, LegalView

logger = logging.getLogger(__name__)


class HomeP0View(HomeView):
    """Accueil avec métrique critique correcte dès le HTML serveur.

    L'animation JavaScript peut toujours réanimer le compteur côté navigateur,
    mais un crawler, un lecteur sans JS ou un aperçu HTML ne doit jamais voir
    « 0 % de projets livrés dans les délais ».
    """

    _COUNTER_ZERO = (
        b'<span class="counter" data-target="100" data-suffix="%">0%</span>'
    )
    _COUNTER_VALUE = (
        b'<span class="counter" data-target="100" data-suffix="%">100%</span>'
    )

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)

        def _fix_counter(rendered_response):
            content = rendered_response.content
            if self._COUNTER_ZERO not in content:
                logger.warning(
                    "Compteur P0 introuvable dans le HTML de l'accueil ; "
                    "vérifier le template pages/home.html."
                )
                return rendered_response
            rendered_response.content = content.replace(
                self._COUNTER_ZERO,
                self._COUNTER_VALUE,
                1,
            )
            return rendered_response

        response.add_post_render_callback(_fix_counter)
        return response


class LegalP0View(LegalView):
    """Page légale alignée sur l'infrastructure de production actuelle."""

    template_name = 'pages/legal_p0.html'
