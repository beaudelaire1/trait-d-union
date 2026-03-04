"""View definitions for the static pages of the site."""
from __future__ import annotations

import json
import re
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any

from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST
from django.views.generic import TemplateView

from services.models import Service


class HomeView(TemplateView):
    """Landing page of the website.

    Displays the slogan, previews of the services, testimonials and calls to action.
    The context will be populated with featured services and testimonials from the database.
    """

    template_name: str = 'pages/home.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:  # type: ignore[override]
        context = super().get_context_data(**kwargs)
        
        # ⚡ PERFORMANCE: Cache homepage data (services, testimonials, portfolio count)
        from django.core.cache import cache
        
        # Charger les services depuis la base de données (cached 5 min)
        services_data = cache.get('homepage_services')
        if services_data is None:
            services_qs = Service.objects.select_related('category').filter(is_active=True, is_featured=True)[:4]
            services_data = [
                {
                    'title': service.name,
                    'description': service.short_description or service.description[:150],
                    'icon': service.category.icon if service.category else '🔧',
                    'slug': service.slug,
                }
                for service in services_qs
            ]
            cache.set('homepage_services', services_data, 300)
        context['services'] = services_data
        
        # Charger les témoignages depuis la base de données (cached 5 min)
        testimonials = cache.get('homepage_testimonials')
        if testimonials is None:
            from apps.pages.models import Testimonial
            testimonials = list(Testimonial.objects.filter(is_published=True)[:3])
            cache.set('homepage_testimonials', testimonials, 300)
        context['testimonials'] = testimonials
        
        # Compteur dynamique de projets portfolio (cached 10 min)
        portfolio_count = cache.get('homepage_portfolio_count')
        if portfolio_count is None:
            from apps.portfolio.models import Project
            portfolio_count = Project.objects.filter(is_published=True).count()
            cache.set('homepage_portfolio_count', portfolio_count, 600)
        context['portfolio_count'] = portfolio_count
        
        # Breadcrumbs SEO (page d'accueil = racine)
        context['breadcrumbs_list'] = [
            {'name': 'Accueil', 'url': '/'},
        ]
        
        return context


class ServicesView(TemplateView):
    """Services overview page."""

    template_name: str = 'pages/services.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['breadcrumbs_list'] = [
            {'name': 'Accueil', 'url': '/'},
            {'name': 'Services', 'url': '/services/'},
        ]
        return context


class MethodView(TemplateView):
    """Methodology page describing the five‑step process."""

    template_name: str = 'pages/method.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['breadcrumbs_list'] = [
            {'name': 'Accueil', 'url': '/'},
            {'name': 'Méthode', 'url': '/method/'},
        ]
        return context


class FAQView(TemplateView):
    """FAQ page with breadcrumbs for SEO rich snippets."""

    template_name: str = 'pages/faq.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['breadcrumbs_list'] = [
            {'name': 'Accueil', 'url': '/'},
            {'name': 'FAQ', 'url': '/faq/'},
        ]
        return context


class MentionsLegalesView(TemplateView):
    """Mentions légales page with breadcrumbs."""

    template_name: str = 'pages/mentions_legales.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['breadcrumbs_list'] = [
            {'name': 'Accueil', 'url': '/'},
            {'name': 'Mentions légales', 'url': '/mentions-legales/'},
        ]
        return context


class ConfidentialiteView(TemplateView):
    """Politique de confidentialité page with breadcrumbs."""

    template_name: str = 'pages/confidentialite.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['breadcrumbs_list'] = [
            {'name': 'Accueil', 'url': '/'},
            {'name': 'Politique de confidentialité', 'url': '/confidentialite/'},
        ]
        return context


class CGVView(TemplateView):
    """Conditions générales de vente page with breadcrumbs."""

    template_name: str = 'pages/cgv.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['breadcrumbs_list'] = [
            {'name': 'Accueil', 'url': '/'},
            {'name': 'Conditions générales de vente', 'url': '/cgv/'},
        ]
        return context


class LegalView(TemplateView):
    """Legal page with breadcrumbs."""

    template_name: str = 'pages/legal.html'

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context['breadcrumbs_list'] = [
            {'name': 'Accueil', 'url': '/'},
            {'name': 'Informations légales', 'url': '/legal/'},
        ]
        return context



class SimulateurView(TemplateView):
    """Page de simulation interactive de devis / facture.

    Les utilisateurs non connectés sont limités à 5 générations.
    Le compteur est stocké en session côté serveur.
    """

    template_name: str = 'pages/simulateur.html'

    def dispatch(self, request, *args, **kwargs):
        from django.middleware.csrf import get_token
        get_token(request)
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            remaining = -1  # illimité
        else:
            remaining = 5 - self.request.session.get('sim_count', 0)
        context['simulations_remaining'] = remaining
        context['services'] = list(
            Service.objects.filter(is_active=True)
            .values('name', 'base_price', 'price_unit')
            .order_by('name')
        )
        context['breadcrumbs_list'] = [
            {'name': 'Accueil', 'url': '/'},
            {'name': 'Simulateur', 'url': '/simulateur/'},
        ]
        return context


@require_POST
def simulateur_increment(request: HttpRequest) -> JsonResponse:
    """Incrémente le compteur de simulations (session) et renvoie le solde."""
    if request.user.is_authenticated:
        return JsonResponse({'allowed': True, 'remaining': -1})
    count = request.session.get('sim_count', 0)
    if count >= 5:
        return JsonResponse({'allowed': False, 'remaining': 0}, status=429)
    request.session['sim_count'] = count + 1
    return JsonResponse({'allowed': True, 'remaining': 4 - count})


# ---------- Helpers for simulateur_pdf ----------

_HEX_COLOR_RE = re.compile(r'^#[0-9a-fA-F]{6}$')
_MAX_ITEMS = 50
_MAX_LOGO_BYTES = 2 * 1024 * 1024  # 2 Mo (base64 ≈ 2.7 Mo text)


def _clean_text(value: object, max_len: int = 500) -> str:
    """Safely coerce to string and truncate."""
    return str(value or '')[:max_len].strip()


def _fmt(value: Decimal) -> str:
    """Format Decimal with 2 decimal places and non-breaking-space thousands separator."""
    q = value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    s = f'{q:,.2f}'.replace(',', '\u00a0').replace('.', ',')
    return s


def _fmt_qty(value: Decimal) -> str:
    if value == value.to_integral_value():
        return str(int(value))
    return str(value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP))


@require_POST
def simulateur_pdf(request: HttpRequest) -> HttpResponse:
    """Generate a simulation PDF using WeasyPrint and return it."""
    from core.services.document_generator import DocumentGenerator

    # --- Rate limit (same logic as simulateur_increment) ---
    if not request.user.is_authenticated:
        count = request.session.get('sim_count', 0)
        if count >= 5:
            return JsonResponse({'error': 'Limite de simulations atteinte.'}, status=429)
        request.session['sim_count'] = count + 1
        remaining = 4 - count
    else:
        remaining = -1

    # --- Parse JSON body ---
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'JSON invalide.'}, status=400)

    # --- Validate & sanitise fields ---
    doc_type = 'devis' if data.get('doc_type') != 'facture' else 'facture'
    is_devis = doc_type == 'devis'
    doc_type_label = 'DEVIS' if is_devis else 'FACTURE'

    accent_color = data.get('accent_color', '#22C55E')
    if not _HEX_COLOR_RE.match(str(accent_color)):
        accent_color = '#22C55E'

    # Logo: only accept data-URI images (PNG/JPEG/SVG/WebP) up to ~2 Mo
    logo = None
    raw_logo = data.get('logo') or ''
    if raw_logo and isinstance(raw_logo, str) and raw_logo.startswith('data:image/'):
        if len(raw_logo) <= _MAX_LOGO_BYTES * 4 // 3 + 100:
            logo = raw_logo

    emitter_raw = data.get('emitter') or {}
    emitter = {
        'name': _clean_text(emitter_raw.get('name'), 200),
        'address': _clean_text(emitter_raw.get('address'), 300),
        'phone': _clean_text(emitter_raw.get('phone'), 30),
        'email': _clean_text(emitter_raw.get('email'), 200),
        'siret': _clean_text(emitter_raw.get('siret'), 50),
    }

    client_raw = data.get('client') or {}
    client = {
        'name': _clean_text(client_raw.get('name'), 200),
        'address': _clean_text(client_raw.get('address'), 300),
        'phone': _clean_text(client_raw.get('phone'), 30),
        'email': _clean_text(client_raw.get('email'), 200),
    }

    validity_days = 30
    try:
        vd = int(data.get('validity_days', 30))
        if 1 <= vd <= 365:
            validity_days = vd
    except (TypeError, ValueError):
        pass

    conditions = _clean_text(data.get('conditions'), 2000)
    notes = _clean_text(data.get('notes'), 2000)

    # --- Items ---
    raw_items = data.get('items') or []
    if not isinstance(raw_items, list):
        raw_items = []
    raw_items = raw_items[:_MAX_ITEMS]

    items = []
    subtotal_ht = Decimal('0')
    raw_tva = Decimal('0')

    for ri in raw_items:
        if not isinstance(ri, dict):
            continue
        try:
            qty = Decimal(str(ri.get('quantity', 0)))
            up = Decimal(str(ri.get('unitPrice', 0)))
            tax = Decimal(str(ri.get('taxRate', 0)))
            ld = Decimal(str(ri.get('lineDiscount', 0)))
        except (InvalidOperation, TypeError):
            continue
        qty = max(qty, Decimal('0'))
        up = max(up, Decimal('0'))
        tax = min(max(tax, Decimal('0')), Decimal('100'))
        ld = min(max(ld, Decimal('0')), Decimal('100'))
        line_ht_brut = qty * up
        line_discount_amt = line_ht_brut * ld / 100
        line_ht = line_ht_brut - line_discount_amt
        line_ttc = line_ht + line_ht * tax / 100
        subtotal_ht += line_ht
        raw_tva += line_ht * tax / 100
        ld_display = str(ld.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)).rstrip('0').rstrip('.') if ld > 0 else ''
        items.append({
            'description': _clean_text(ri.get('description'), 500),
            'quantity_display': _fmt_qty(qty),
            'unit_price_display': _fmt(up),
            'line_discount_display': ld_display,
            'tax_rate': str(tax.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)).rstrip('0').rstrip('.'),
            'total_ttc_display': _fmt(line_ttc),
        })

    # --- Discount ---
    disc_raw = data.get('discount') or {}
    disc_type = 'percent' if disc_raw.get('type') != 'fixed' else 'fixed'
    try:
        disc_val = Decimal(str(disc_raw.get('value', 0)))
        disc_val = max(disc_val, Decimal('0'))
    except (InvalidOperation, TypeError):
        disc_val = Decimal('0')

    if disc_type == 'percent':
        discount_amount = subtotal_ht * disc_val / 100
    else:
        discount_amount = min(disc_val, subtotal_ht)

    # TVA proportionally reduced by discount
    if subtotal_ht > 0 and discount_amount > 0:
        total_tva = raw_tva * (subtotal_ht - discount_amount) / subtotal_ht
    else:
        total_tva = raw_tva

    total_ttc = subtotal_ht - discount_amount + total_tva

    today = date.today()
    issue_date = today.strftime('%d/%m/%Y')
    year = today.year
    doc_ref = f"{'DEV' if is_devis else 'FAC'}-{year}-SIM"

    context = {
        'doc_type_label': doc_type_label,
        'doc_ref': doc_ref,
        'is_devis': is_devis,
        'accent_color': accent_color,
        'logo': logo,
        'emitter': emitter,
        'client': client,
        'items': items,
        'issue_date': issue_date,
        'validity_days': validity_days,
        'subtotal_ht': _fmt(subtotal_ht),
        'discount_amount': _fmt(discount_amount) if discount_amount > 0 else '',
        'total_tva': _fmt(total_tva),
        'total_ttc': _fmt(total_ttc),
        'conditions': conditions,
        'notes': notes,
    }

    html_content = render_to_string('pdf/simulation_pdf.html', context)
    pdf_bytes = DocumentGenerator._render_pdf(html_content)  # noqa: SLF001

    response = HttpResponse(pdf_bytes, content_type='application/pdf')
    filename = f"{doc_type}_simulation.pdf"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response['X-Simulations-Remaining'] = str(remaining)
    return response


def page_not_found(request: HttpRequest, exception: Exception) -> HttpResponse:
    """Custom 404 page handler."""
    return render(request, 'errors/404.html', status=404)


def server_error(request: HttpRequest) -> HttpResponse:
    """Custom 500 page handler."""
    return render(request, 'errors/500.html', status=500)


def permission_denied(request: HttpRequest, exception: Exception) -> HttpResponse:
    """Custom 403 page handler."""
    return render(request, 'errors/403.html', status=403)