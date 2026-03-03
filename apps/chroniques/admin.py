from django import forms
from django.contrib import admin
from django.db import models

from .models import Article, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)


class ArticleAdminForm(forms.ModelForm):
    class Meta:
        model = Article
        fields = "__all__"
        widgets = {
            "body": forms.Textarea(
                attrs={
                    "class": "tus-tinymce",
                    "rows": 18,
                }
            )
        }


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    form = ArticleAdminForm
    list_display = ("title", "category", "is_published", "publish_date", "author")
    list_filter = ("is_published", "publish_date", "category")
    search_fields = ("title", "subtitle", "excerpt", "body")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "publish_date"
    fieldsets = (
        (None, {
            'fields': ('title', 'subtitle', 'slug', 'category', 'author', 'cover_image', 'excerpt', 'body'),
        }),
        ('🔍 SEO', {
            'fields': ('meta_description',),
            'description': 'Meta description pour Google (160 chars max). Si vide, le résumé sera utilisé.',
        }),
        ('Publication', {
            'fields': ('is_published', 'publish_date'),
        }),
    )

    class Media:
        css = {
            "all": ("css/admin-tinymce.css",)
        }
        js = (
            "https://cdn.jsdelivr.net/npm/tinymce@6.8.2/tinymce.min.js",
            "js/admin/article-tinymce.js",
        )
