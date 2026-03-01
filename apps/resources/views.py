"""View definitions for downloadable resources."""
from __future__ import annotations

from django.http import FileResponse, HttpRequest, HttpResponse, Http404
from django.views.generic import TemplateView, View
from django.conf import settings
from django.utils.encoding import smart_str


class ResourcesView(TemplateView):
    template_name: str = 'resources/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumbs_list'] = [
            {'name': 'Accueil', 'url': '/'},
            {'name': 'Ressources', 'url': '/resources/'},
        ]
        return context


class DownloadView(View):
    """Serve PDF files listed in ALLOWED_FILES.

    🛡️ SECURITY: Only whitelisted filenames are served.  The resolved
    path is validated to stay within the expected directory to prevent
    path-traversal attacks.
    """

    ALLOWED_FILES = {
        'checklist': 'checklist-projet-web-premium.pdf',
        'cahier-des-charges': 'modele-cahier-des-charges.pdf',
    }

    def get(self, request: HttpRequest, filename: str) -> HttpResponse:
        pdf_name = self.ALLOWED_FILES.get(filename)
        if not pdf_name:
            raise Http404
        resources_dir = settings.BASE_DIR / 'media' / 'resources'
        path = (resources_dir / pdf_name).resolve()
        # 🛡️ SECURITY: Ensure resolved path stays within the resources directory
        if not str(path).startswith(str(resources_dir.resolve())):
            raise Http404
        if not path.exists():
            raise Http404
        response = FileResponse(open(path, 'rb'), as_attachment=True, filename=pdf_name)
        response['Content-Type'] = 'application/pdf'
        return response