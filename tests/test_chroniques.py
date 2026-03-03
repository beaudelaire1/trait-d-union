"""Tests for chroniques app: Category model, Article subtitle/category, filtering, sorting, search."""
import pytest
from django.test import Client
from django.utils import timezone
from datetime import timedelta
from apps.chroniques.models import Article, Category


@pytest.mark.django_db
class TestCategoryModel:
    def test_category_str(self):
        cat = Category.objects.create(name="Design", slug="design")
        assert str(cat) == "Design"

    def test_category_ordering(self):
        Category.objects.create(name="Zéro", slug="zero")
        Category.objects.create(name="Alpha", slug="alpha")
        names = list(Category.objects.values_list("name", flat=True))
        assert names == ["Alpha", "Zéro"]


@pytest.mark.django_db
class TestArticleSubtitleAndCategory:
    def test_article_subtitle_blank_by_default(self):
        article = Article.objects.create(
            title="Test", slug="test", body="Content",
        )
        assert article.subtitle == ""

    def test_article_subtitle_saved(self):
        article = Article.objects.create(
            title="Test", slug="test-sub", body="Content",
            subtitle="Mon sous-titre",
        )
        assert article.subtitle == "Mon sous-titre"

    def test_article_category_nullable(self):
        article = Article.objects.create(
            title="No Cat", slug="no-cat", body="Content",
        )
        assert article.category is None

    def test_article_with_category(self):
        cat = Category.objects.create(name="Tech", slug="tech")
        article = Article.objects.create(
            title="With Cat", slug="with-cat", body="Content", category=cat,
        )
        assert article.category == cat
        assert article in cat.articles.all()


@pytest.mark.django_db
class TestArticleListFiltering:
    def setup_method(self):
        self.client = Client()
        self.cat1 = Category.objects.create(name="Design", slug="design")
        self.cat2 = Category.objects.create(name="Dev", slug="dev")
        Article.objects.create(
            title="Article Design", slug="art-design", body="A",
            category=self.cat1, is_published=True,
        )
        Article.objects.create(
            title="Article Dev", slug="art-dev", body="B",
            category=self.cat2, is_published=True,
        )
        Article.objects.create(
            title="Article Sans Cat", slug="art-none", body="C",
            is_published=True,
        )

    def test_list_no_filter_shows_all(self):
        resp = self.client.get("/chroniques/")
        assert resp.status_code == 200
        assert b"Article Design" in resp.content
        assert b"Article Dev" in resp.content
        assert b"Article Sans Cat" in resp.content

    def test_list_filter_by_category(self):
        resp = self.client.get("/chroniques/?category=design")
        assert resp.status_code == 200
        assert b"Article Design" in resp.content
        assert b"Article Dev" not in resp.content

    def test_list_filter_invalid_category_shows_all(self):
        resp = self.client.get("/chroniques/?category=nonexistent")
        assert resp.status_code == 200
        assert b"Article Design" in resp.content
        assert b"Article Dev" in resp.content

    def test_list_shows_category_filters(self):
        resp = self.client.get("/chroniques/")
        assert b"Design" in resp.content
        assert b"Dev" in resp.content
        assert b"Tous" in resp.content


@pytest.mark.django_db
class TestArticleDetail:
    def test_detail_shows_subtitle(self):
        article = Article.objects.create(
            title="Titre", slug="titre", body="Content",
            subtitle="Sous-titre test", is_published=True,
        )
        resp = Client().get(f"/chroniques/{article.slug}/")
        assert resp.status_code == 200
        assert b"Sous-titre test" in resp.content

    def test_detail_shows_category(self):
        cat = Category.objects.create(name="UX", slug="ux")
        article = Article.objects.create(
            title="Titre", slug="titre-ux", body="Content",
            category=cat, is_published=True,
        )
        resp = Client().get(f"/chroniques/{article.slug}/")
        assert resp.status_code == 200
        assert b"UX" in resp.content

    def test_detail_subtitle_is_italic(self):
        article = Article.objects.create(
            title="Titre", slug="titre-it", body="Content",
            subtitle="Subtitle italic", is_published=True,
        )
        resp = Client().get(f"/chroniques/{article.slug}/")
        content = resp.content.decode()
        assert "italic" in content
        assert "Subtitle italic" in content


@pytest.mark.django_db
class TestArticleListSorting:
    """Test sort options on the article list view."""

    def setup_method(self):
        self.client = Client()
        now = timezone.now()
        Article.objects.create(
            title="Alpha", slug="alpha", body="A",
            is_published=True, publish_date=now - timedelta(days=3),
        )
        Article.objects.create(
            title="Beta", slug="beta", body="B",
            is_published=True, publish_date=now - timedelta(days=1),
        )
        Article.objects.create(
            title="Gamma", slug="gamma", body="G",
            is_published=True, publish_date=now - timedelta(days=2),
        )

    def test_sort_recent_default(self):
        resp = self.client.get("/chroniques/")
        content = resp.content.decode()
        pos_beta = content.index("Beta")
        pos_gamma = content.index("Gamma")
        pos_alpha = content.index("Alpha")
        assert pos_beta < pos_gamma < pos_alpha

    def test_sort_oldest(self):
        resp = self.client.get("/chroniques/?sort=oldest")
        content = resp.content.decode()
        pos_alpha = content.index("Alpha")
        pos_gamma = content.index("Gamma")
        pos_beta = content.index("Beta")
        assert pos_alpha < pos_gamma < pos_beta

    def test_sort_title_asc(self):
        resp = self.client.get("/chroniques/?sort=title_asc")
        content = resp.content.decode()
        pos_alpha = content.index("Alpha")
        pos_beta = content.index("Beta")
        pos_gamma = content.index("Gamma")
        assert pos_alpha < pos_beta < pos_gamma

    def test_sort_title_desc(self):
        resp = self.client.get("/chroniques/?sort=title_desc")
        content = resp.content.decode()
        pos_gamma = content.index("Gamma")
        pos_beta = content.index("Beta")
        pos_alpha = content.index("Alpha")
        assert pos_gamma < pos_beta < pos_alpha

    def test_sort_invalid_falls_back_to_recent(self):
        resp = self.client.get("/chroniques/?sort=invalid")
        assert resp.status_code == 200
        assert resp.context["current_sort"] == "recent"


@pytest.mark.django_db
class TestArticleListSearch:
    """Test text search on the article list view."""

    def setup_method(self):
        self.client = Client()
        Article.objects.create(
            title="Audience et réseaux", slug="audience", body="Content",
            subtitle="Instagram ne suffit pas", is_published=True,
        )
        Article.objects.create(
            title="SEO local", slug="seo-local", body="Content SEO",
            excerpt="Optimisation pour la Guyane", is_published=True,
        )

    def test_search_by_title(self):
        resp = self.client.get("/chroniques/?q=audience")
        assert resp.status_code == 200
        assert b"Audience" in resp.content
        assert b"SEO local" not in resp.content

    def test_search_by_subtitle(self):
        resp = self.client.get("/chroniques/?q=instagram")
        assert resp.status_code == 200
        assert b"Audience" in resp.content
        assert b"SEO local" not in resp.content

    def test_search_by_excerpt(self):
        resp = self.client.get("/chroniques/?q=guyane")
        assert resp.status_code == 200
        assert b"SEO local" in resp.content
        assert b"Audience" not in resp.content

    def test_search_no_results(self):
        resp = self.client.get("/chroniques/?q=xyzunknown")
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "Aucun article ne correspond" in content

    def test_search_query_preserved_in_context(self):
        resp = self.client.get("/chroniques/?q=audience")
        assert resp.context["search_query"] == "audience"

    def test_combined_search_and_category(self):
        cat = Category.objects.create(name="Web", slug="web")
        Article.objects.filter(slug="audience").update(category=cat)
        # Search + filter → only matching article
        resp = self.client.get("/chroniques/?q=audience&category=web")
        assert b"Audience" in resp.content
        assert b"SEO local" not in resp.content

    def test_combined_search_and_sort(self):
        resp = self.client.get("/chroniques/?q=&sort=title_asc")
        assert resp.status_code == 200
        assert resp.context["current_sort"] == "title_asc"


@pytest.mark.django_db
class TestQueryStringPreservation:
    """Ensure filter parameters are forwarded to the template for pagination."""

    def test_query_string_with_category_and_sort(self):
        cat = Category.objects.create(name="Tech", slug="tech")
        Article.objects.create(
            title="A1", slug="a1", body="X",
            is_published=True, category=cat,
        )
        resp = self.client.get("/chroniques/?category=tech&sort=oldest")
        qs = resp.context["query_string"]
        assert "category=tech" in qs
        assert "sort=oldest" in qs

    def setup_method(self):
        self.client = Client()
