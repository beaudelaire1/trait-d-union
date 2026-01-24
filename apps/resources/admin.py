"""Admin configuration for knowledge base."""
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    KnowledgeCategory, KnowledgeArticle, ArticleTag, FAQ,
    AcademyCourse, AcademyLesson, ClientCourseEnrollment, ClientQuizResult
)


@admin.register(KnowledgeCategory)
class KnowledgeCategoryAdmin(admin.ModelAdmin):
    """Admin for knowledge base categories."""
    list_display = ['icon_name', 'name', 'article_count', 'is_active', 'order']
    list_editable = ['is_active', 'order']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    
    def icon_name(self, obj):
        return f"{obj.icon} {obj.name}"
    icon_name.short_description = "Catégorie"
    
    def article_count(self, obj):
        count = obj.articles.count()
        return format_html('<strong>{}</strong> article(s)', count)
    article_count.short_description = "Articles"


@admin.register(KnowledgeArticle)
class KnowledgeArticleAdmin(admin.ModelAdmin):
    """Admin for knowledge base articles."""
    list_display = ['title', 'category', 'difficulty_badge', 'stats', 'is_published', 'is_featured']
    list_filter = ['category', 'difficulty', 'is_published', 'is_featured', 'created_at']
    search_fields = ['title', 'summary', 'content']
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ['is_published', 'is_featured']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Contenu', {
            'fields': ('category', 'title', 'slug', 'summary', 'content')
        }),
        ('Média', {
            'fields': ('video_url', 'reading_time', 'difficulty')
        }),
        ('SEO', {
            'fields': ('meta_description',),
            'classes': ('collapse',)
        }),
        ('Publication', {
            'fields': ('author', 'is_published', 'is_featured')
        }),
        ('Statistiques', {
            'fields': ('views_count', 'helpful_count'),
            'classes': ('collapse',)
        }),
    )
    
    def difficulty_badge(self, obj):
        colors = {
            'beginner': 'green',
            'intermediate': 'orange',
            'advanced': 'red',
        }
        color = colors.get(obj.difficulty, 'gray')
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            obj.get_difficulty_display()
        )
    difficulty_badge.short_description = "Niveau"
    
    def stats(self, obj):
        return format_html(
            '👁️ {} vues • 👍 {} utiles',
            obj.views_count,
            obj.helpful_count
        )
    stats.short_description = "Stats"


@admin.register(ArticleTag)
class ArticleTagAdmin(admin.ModelAdmin):
    """Admin for article tags."""
    list_display = ['name', 'article_count']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    
    def article_count(self, obj):
        return obj.articles.count()
    article_count.short_description = "Articles"


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    """Admin for FAQs."""
    list_display = ['question', 'category', 'audience_badge', 'views', 'is_active', 'order']
    list_filter = ['category', 'audience', 'is_active']
    search_fields = ['question', 'answer']
    list_editable = ['is_active', 'order']
    
    fieldsets = (
        (None, {
            'fields': ('question', 'answer', 'category')
        }),
        ('Configuration', {
            'fields': ('audience', 'order', 'is_active')
        }),
        ('Stats', {
            'fields': ('views_count',),
            'classes': ('collapse',)
        }),
    )
    
    def audience_badge(self, obj):
        colors = {
            'all': 'blue',
            'prospect': 'purple',
            'client': 'green',
        }
        color = colors.get(obj.audience, 'gray')
        return format_html(
            '<span style="background: {}; color: white; padding: 2px 8px; border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_audience_display()
        )
    audience_badge.short_description = "Audience"
    
    def views(self, obj):
        return format_html('<strong>{}</strong>', obj.views_count)
    views.short_description = "Vues"


# ============================
# E-learning Academy Admin
# ============================

class AcademyLessonInline(admin.TabularInline):
    """Inline pour les leçons."""
    model = AcademyLesson
    extra = 0
    fields = ['title', 'order', 'video_duration_minutes', 'content']


@admin.register(AcademyCourse)
class AcademyCourseAdmin(admin.ModelAdmin):
    """Admin pour les cours."""
    list_display = ['title', 'category', 'level', 'students_badge', 'rating_badge', 'is_published', 'is_featured']
    list_filter = ['category', 'level', 'is_published', 'is_featured', 'created_at']
    search_fields = ['title', 'description']
    prepopulated_fields = {'slug': ('title',)}
    list_editable = ['is_published', 'is_featured']
    inlines = [AcademyLessonInline]
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Identité', {
            'fields': ('title', 'slug', 'description', 'category', 'level')
        }),
        ('Contenu', {
            'fields': ('introduction', 'learning_objectives', 'estimated_duration_hours')
        }),
        ('Instructeur', {
            'fields': ('instructor',),
            'classes': ('collapse',)
        }),
        ('Publication', {
            'fields': ('is_published', 'is_featured')
        }),
        ('Stats', {
            'fields': ('students_count', 'rating'),
            'classes': ('collapse',)
        }),
    )
    
    def students_badge(self, obj):
        return format_html('<strong>{}</strong> étudiant(s)', obj.students_count)
    students_badge.short_description = "Étudiants"
    
    def rating_badge(self, obj):
        if obj.rating > 0:
            return format_html('⭐ {}/5', obj.rating)
        return '-'
    rating_badge.short_description = "Note"


@admin.register(AcademyLesson)
class AcademyLessonAdmin(admin.ModelAdmin):
    """Admin pour les leçons."""
    list_display = ['title', 'course', 'order', 'video_duration_minutes', 'has_quiz_display']
    list_filter = ['course', 'order']
    search_fields = ['title', 'content']
    ordering = ['course', 'order']
    
    fieldsets = (
        ('Infos', {
            'fields': ('course', 'title', 'order')
        }),
        ('Contenu', {
            'fields': ('content',),
            'classes': ('wide',)
        }),
        ('Vidéo', {
            'fields': ('video_url', 'video_duration_minutes')
        }),
        ('Ressources', {
            'fields': ('resources',),
            'classes': ('collapse',)
        }),
        ('Quiz', {
            'fields': ('quiz_content',),
            'classes': ('collapse',)
        }),
    )
    
    def has_quiz_display(self, obj):
        if obj.quiz_content:
            return format_html('<span style="color: green;">✓ Quiz</span>')
        return '-'
    has_quiz_display.short_description = "Quiz"


@admin.register(ClientCourseEnrollment)
class ClientCourseEnrollmentAdmin(admin.ModelAdmin):
    """Admin pour les inscriptions."""
    list_display = ['client', 'course', 'status', 'progress_bar', 'certificate_badge']
    list_filter = ['status', 'course', 'enrolled_at']
    search_fields = ['client__user__email', 'course__title']
    readonly_fields = ['enrolled_at']
    
    fieldsets = (
        ('Inscription', {
            'fields': ('client', 'course', 'enrolled_at')
        }),
        ('Progression', {
            'fields': ('status', 'progress_percent')
        }),
        ('Certificat', {
            'fields': ('certificate_earned', 'certificate_url'),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('started_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )
    
    def progress_bar(self, obj):
        width = int(obj.progress_percent / 100 * 100)
        return format_html(
            '<div style="width:100px; background: #ddd; border-radius: 5px; overflow: hidden;">'
            '<div style="width:{}%; background: #4CAF50; height: 20px; text-align: center; color: white; font-size: 11px; line-height: 20px;">'
            '{}%</div></div>',
            width, obj.progress_percent
        )
    progress_bar.short_description = "Progression"
    
    def certificate_badge(self, obj):
        if obj.certificate_earned:
            return format_html('✓ <a href="{}" target="_blank">Certificat</a>', obj.certificate_url)
        return '-'
    certificate_badge.short_description = "Certificat"


@admin.register(ClientQuizResult)
class ClientQuizResultAdmin(admin.ModelAdmin):
    """Admin pour les résultats de quiz."""
    list_display = ['enrollment', 'lesson', 'score_badge', 'completed_at']
    list_filter = ['score_percent', 'completed_at', 'enrollment__course']
    search_fields = ['enrollment__client__user__email', 'lesson__title']
    readonly_fields = ['completed_at']
    
    def score_badge(self, obj):
        color = 'green' if obj.score_percent >= 70 else 'orange' if obj.score_percent >= 50 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}/100</span>',
            color, obj.score_percent
        )
    score_badge.short_description = "Score"
