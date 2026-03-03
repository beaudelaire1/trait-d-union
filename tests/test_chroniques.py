"""Tests for chroniques app: Category model, Article subtitle/category, filtering."""
import pytest
from django.test import Client
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
