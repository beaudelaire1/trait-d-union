from __future__ import annotations

from django.shortcuts import get_object_or_404, render
from django.core.paginator import Paginator
from django.db import ProgrammingError, OperationalError
from .models import Article, Category


def article_list(request):
    try:
        qs = Article.objects.select_related('author', 'category').filter(is_published=True).order_by("-publish_date")

        category_slug = request.GET.get("category")
        active_category = None
        if category_slug:
            active_category = Category.objects.filter(slug=category_slug).first()
            if active_category:
                qs = qs.filter(category=active_category)

        categories = Category.objects.all()

        paginator = Paginator(qs, 9)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
    except (ProgrammingError, OperationalError):
        # Table doesn't exist yet (migration pending)
        page_obj = None
        categories = []
        active_category = None
    return render(request, "chroniques/list.html", {
        "page_obj": page_obj,
        "categories": categories,
        "active_category": active_category,
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
