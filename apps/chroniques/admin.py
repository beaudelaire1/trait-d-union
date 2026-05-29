from django import forms
from django.contrib import admin, messages
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
    list_display = ("title", "category", "views_count", "is_published", "publish_date", "author")
    list_filter = ("is_published", "publish_date", "category")
    search_fields = ("title", "subtitle", "excerpt", "body")
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "publish_date"
    actions = ['send_as_newsletter']
    readonly_fields = ("views_count",)
    fieldsets = (
        (None, {
            'fields': ('title', 'subtitle', 'slug', 'category', 'author', 'cover_image', 'credits_image', 'excerpt', 'body'),
        }),
        ('🔍 SEO', {
            'fields': ('meta_description',),
            'description': 'Meta description pour Google (160 chars max). Si vide, le résumé sera utilisé.',
        }),
        ('Publication', {
            'fields': ('is_published', 'publish_date'),
        }),
        ('Statistiques', {
            'fields': ('views_count',),
            'classes': ('collapse',),
        }),
    )

    @admin.action(description="📤 Envoyer comme newsletter aux abonnés")
    def send_as_newsletter(self, request, queryset):
        """Envoi synchrone de l'article comme newsletter à tous les abonnés actifs.

        Pas de worker django-q2 disponible en prod : on exécute directement
        la tâche dans la requête. Pour ~50 abonnés c'est < 12s, acceptable.
        """
        from apps.leads.models import EmailSubscriber
        from apps.leads.tasks import send_article_as_newsletter_task

        subscriber_count = EmailSubscriber.objects.filter(is_active=True).count()
        if subscriber_count == 0:
            self.message_user(request, "❌ Aucun abonné actif.", level=messages.WARNING)
            return

        for article in queryset:
            if not article.is_published:
                self.message_user(
                    request,
                    f"⏭️ « {article.title} » ignoré (non publié).",
                    level=messages.WARNING,
                )
                continue

            try:
                result = send_article_as_newsletter_task(article_id=article.pk)
            except Exception as exc:
                self.message_user(
                    request,
                    f"❌ Erreur lors de l'envoi de « {article.title} » : {exc}",
                    level=messages.ERROR,
                )
                continue

            if result.get('error'):
                self.message_user(
                    request,
                    f"❌ « {article.title} » : {result['error']}",
                    level=messages.ERROR,
                )
                continue

            total = result.get('total', 0)
            success = result.get('success', 0)
            failed = len(result.get('failed', []))
            campaign_id = result.get('campaign_id')

            self.message_user(
                request,
                f"📤 « {article.title} » envoyé : {success}/{total} OK"
                f"{f', {failed} échec(s)' if failed else ''}"
                f"{f' — campagne #{campaign_id}' if campaign_id else ''}.",
                level=messages.SUCCESS if success and not failed else messages.WARNING,
            )

    class Media:
        css = {
            "all": ("css/admin-tinymce.css",)
        }
        js = (
            "https://cdn.jsdelivr.net/npm/tinymce@6.8.2/tinymce.min.js",
            "js/admin/article-tinymce.js",
        )
