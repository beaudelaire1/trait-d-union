from __future__ import annotations

from django.shortcuts import get_object_or_404, render
from django.core.paginator import Paginator
from django.db import ProgrammingError, OperationalError
from .models import Article


def article_list(request):
    try:
        qs = Article.objects.filter(is_published=True).order_by("-publish_date")
        paginator = Paginator(qs, 9)
        page_number = request.GET.get("page")
        page_obj = paginator.get_page(page_number)
    except (ProgrammingError, OperationalError):
        # Table doesn't exist yet (migration pending)
        page_obj = None
    return render(request, "chroniques/list.html", {"page_obj": page_obj})


def article_detail(request, slug: str):
    article = get_object_or_404(Article, slug=slug, is_published=True)
    return render(request, "chroniques/detail.html", {"article": article})
