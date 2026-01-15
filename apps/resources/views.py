"""View definitions for downloadable resources."""
from __future__ import annotations

from django.http import FileResponse, HttpRequest, HttpResponse, Http404
from django.views.generic import TemplateView, View
from django.conf import settings
from django.utils.encoding import smart_str


class ResourcesView(TemplateView):
    template_name: str = 'resources/index.html'


class DownloadView(View):
    """Serve PDF files listed in ALLOWED_FILES."""

    ALLOWED_FILES = {
        'checklist': 'checklist-projet-web-premium.pdf',
        'cahier-des-charges': 'modele-cahier-des-charges.pdf',
    }

    def get(self, request: HttpRequest, filename: str) -> HttpResponse:
        pdf_name = self.ALLOWED_FILES.get(filename)
        if not pdf_name:
            raise Http404
        path = settings.BASE_DIR / 'media' / 'resources' / pdf_name
        if not path.exists():
            raise Http404
        response = FileResponse(open(path, 'rb'), as_attachment=True, filename=pdf_name)
        response['Content-Type'] = 'application/pdf'
        return response