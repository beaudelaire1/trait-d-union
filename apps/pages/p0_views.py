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
    """Mentions légales cohérentes avec l'infrastructure de production.

    Le template historique contient encore des références à l'ancien
    déploiement Render/Francfort/Hostinger/Celery. La correction est appliquée
    sur la réponse rendue afin de remettre immédiatement l'information publique
    en conformité sans modifier le reste de la page légale.
    """

    _REPLACEMENTS = (
        (
            b'<strong class="text-tus-white">Render Services, Inc.</strong>',
            b'<strong class="text-tus-white">OVH SAS (OVHcloud)</strong>',
        ),
        (
            b'525 Brannan Street, Suite 300, San Francisco, CA 94107, \xc3\x89tats-Unis',
            b'2 rue Kellermann, 59100 Roubaix, France',
        ),
        (
            b'<a href="https://render.com" class="text-tus-blue-a11y hover:underline">render.com</a>',
            b'<a href="https://www.ovhcloud.com" class="text-tus-blue-a11y hover:underline">ovhcloud.com</a>',
        ),
        (
            b'datacenter de Francfort (Allemagne, Union europ\xc3\xa9enne)',
            b'datacenter de Strasbourg (France, Union europ\xc3\xa9enne)',
        ),
        (
            b'La gestion du nom de domaine (DNS) est assur\xc3\xa9e par Hostinger International Ltd. (Larnaca, Chypre, UE).',
            b'La gestion DNS du domaine est distincte de l\'h\xc3\xa9bergement applicatif OVHcloud.',
        ),
        (
            b'Django (Python), PostgreSQL, Celery, Redis, Gunicorn, WhiteNoise',
            b'Django (Python), PostgreSQL, Django-Q2, Redis, Gunicorn, WhiteNoise',
        ),
        (
            b'Render (Francfort, UE), PostgreSQL manag\xc3\xa9, stockage objet compatible S3 (AWS S3 / Cloudflare R2), conteneurisation Docker',
            b'OVHcloud (Strasbourg, France), PostgreSQL, stockage objet compatible S3, conteneurisation Docker',
        ),
    )

    def render_to_response(self, context, **response_kwargs):
        response = super().render_to_response(context, **response_kwargs)

        def _fix_legal(rendered_response):
            content = rendered_response.content
            missing = []
            for old, new in self._REPLACEMENTS:
                if old not in content:
                    missing.append(old[:80])
                    continue
                content = content.replace(old, new)
            rendered_response.content = content
            if missing:
                logger.warning(
                    "Certaines mentions d'infrastructure P0 n'ont pas \xc3\xa9t\xc3\xa9 trouv\xc3\xa9es dans legal.html."
                )
            return rendered_response

        response.add_post_render_callback(_fix_legal)
        return response
