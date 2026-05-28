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
        from django_q.tasks import async_task
        from apps.leads.models import EmailSubscriber

        subscriber_count = EmailSubscriber.objects.filter(is_active=True).count()
        if subscriber_count == 0:
            self.message_user(request, "❌ Aucun abonné actif.", level=admin.options.messages.WARNING)
            return

        sent = 0
        for article in queryset:
            if not article.is_published:
                self.message_user(
                    request,
                    f"⏭️ « {article.title} » ignoré (non publié).",
                    level=admin.options.messages.WARNING,
                )
                continue
            async_task(
                'apps.leads.tasks.send_article_as_newsletter_task',
                article_id=article.pk,
                task_name=f'newsletter_article_{article.pk}',
            )
            sent += 1

        if sent:
            self.message_user(
                request,
                f"📤 {sent} article(s) envoyé(s) comme newsletter à {subscriber_count} abonné(s). "
                f"Suivi dans l'admin Leads > Campagnes newsletter.",
                level=admin.options.messages.SUCCESS,
            )

    class Media:
        css = {
            "all": ("css/admin-tinymce.css",)
        }
        js = (
            "https://cdn.jsdelivr.net/npm/tinymce@6.8.2/tinymce.min.js",
            "js/admin/article-tinymce.js",
        )
