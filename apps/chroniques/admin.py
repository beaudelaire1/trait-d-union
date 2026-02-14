from django import forms
from django.contrib import admin
from django.db import models

from .models import Article


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
    list_display = ("title", "is_published", "publish_date", "author")
    list_filter = ("is_published", "publish_date")
    search_fields = ("title", "excerpt", "body")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "publish_date"

    class Media:
        css = {
            "all": ("css/admin-tinymce.css",)
        }
        js = (
            "https://cdn.jsdelivr.net/npm/tinymce@6.8.2/tinymce.min.js",
            "js/admin/article-tinymce.js",
        )
