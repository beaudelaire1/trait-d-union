from __future__ import annotations

from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.core.paginator import Paginator
from django.db import ProgrammingError, OperationalError
from .models import Article, Category

# ── Valid sort options ──────────────────────────────────────────────
SORT_OPTIONS = {
    "recent": ("-publish_date",),
    "oldest": ("publish_date",),
    "title_asc": ("title",),
    "title_desc": ("-title",),
}
SORT_LABELS = {
    "recent": "Plus récents",
    "oldest": "Plus anciens",
    "title_asc": "Titre A → Z",
    "title_desc": "Titre Z → A",
}
DEFAULT_SORT = "recent"


def _build_query_string(params: dict, exclude: str = "") -> str:
    """Build a URL query string preserving all params except *exclude*."""
    parts = []
    for key, val in params.items():
        if key != exclude and val:
            parts.append(f"{key}={val}")
    return "&".join(parts)


def article_list(request):
    try:
        qs = Article.objects.select_related('author', 'category').filter(is_published=True)

        # ── Category filter ─────────────────────────────────────────
        category_slug = request.GET.get("category", "")
        active_category = None
        if category_slug:
            active_category = Category.objects.filter(slug=category_slug).first()
            if active_category:
                qs = qs.filter(category=active_category)

        # ── Text search ─────────────────────────────────────────────
        search_query = request.GET.get("q", "").strip()
        if search_query:
            qs = qs.filter(
                Q(title__icontains=search_query)
                | Q(subtitle__icontains=search_query)
                | Q(excerpt__icontains=search_query)
            )

        # ── Sort ────────────────────────────────────────────────────
        current_sort = request.GET.get("sort", DEFAULT_SORT)
        if current_sort not in SORT_OPTIONS:
            current_sort = DEFAULT_SORT
        qs = qs.order_by(*SORT_OPTIONS[current_sort])

        categories = Category.objects.all()

        # ── Pagination (preserve filters) ───────────────────────────
        paginator = Paginator(qs, 9)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)

        # Build a query string that keeps category/sort/q when paginating
        filter_params = {}
        if category_slug:
            filter_params["category"] = category_slug
        if search_query:
            filter_params["q"] = search_query
        if current_sort != DEFAULT_SORT:
            filter_params["sort"] = current_sort
        query_string = _build_query_string(filter_params)

    except (ProgrammingError, OperationalError):
        # Table doesn't exist yet (migration pending)
        page_obj = None
        categories = []
        active_category = None
        search_query = ""
        current_sort = DEFAULT_SORT
        query_string = ""

    return render(request, "chroniques/list.html", {
        "page_obj": page_obj,
        "categories": categories,
        "active_category": active_category,
        "search_query": search_query,
        "current_sort": current_sort,
        "sort_options": SORT_LABELS,
        "query_string": query_string,
        "breadcrumbs_list": [
            {'name': 'Accueil', 'url': '/'},
            {'name': 'Chroniques', 'url': '/chroniques/'},
        ],
    })


def article_detail(request, slug: str):
    article = get_object_or_404(Article.objects.select_related('category'), slug=slug, is_published=True)
    return render(request, "chroniques/detail.html", {
        "article": article,
        "breadcrumbs_list": [
            {'name': 'Accueil', 'url': '/'},
            {'name': 'Chroniques', 'url': '/chroniques/'},
            {'name': article.title, 'url': article.get_absolute_url()},
        ],
    })
