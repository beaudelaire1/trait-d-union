"""Models for the knowledge base / help center."""
from django.db import models
from django.utils.text import slugify
from django.contrib.auth.models import User


class KnowledgeCategory(models.Model):
    """Catégorie d'articles de la base de connaissances."""
    
    name = models.CharField("Nom", max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField("Description", blank=True)
    icon = models.CharField(
        "Icône emoji",
        max_length=10,
        default="📚",
        help_text="Emoji pour la catégorie"
    )
    order = models.PositiveIntegerField("Ordre", default=0)
    is_active = models.BooleanField("Active", default=True)
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name = "Catégorie"
        verbose_name_plural = "Catégories"
    
    def __str__(self):
        return f"{self.icon} {self.name}"
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class KnowledgeArticle(models.Model):
    """Article de la base de connaissances."""
    
    DIFFICULTY_CHOICES = [
        ('beginner', '🟢 Débutant'),
        ('intermediate', '🟡 Intermédiaire'),
        ('advanced', '🔴 Avancé'),
    ]
    
    category = models.ForeignKey(
        KnowledgeCategory,
        on_delete=models.CASCADE,
        related_name='articles',
        verbose_name="Catégorie"
    )
    title = models.CharField("Titre", max_length=200)
    slug = models.SlugField(unique=True)
    summary = models.CharField(
        "Résumé",
        max_length=255,
        help_text="Description courte pour les listes"
    )
    content = models.TextField("Contenu", help_text="Markdown supporté")
    difficulty = models.CharField(
        "Difficulté",
        max_length=20,
        choices=DIFFICULTY_CHOICES,
        default='beginner'
    )
    
    # Méta
    reading_time = models.PositiveIntegerField(
        "Temps de lecture (min)",
        default=5
    )
    video_url = models.URLField(
        "URL vidéo tutoriel",
        blank=True,
        help_text="YouTube, Vimeo, Loom..."
    )
    
    # SEO
    meta_description = models.CharField(
        "Meta description",
        max_length=160,
        blank=True
    )
    
    # Status
    is_published = models.BooleanField("Publié", default=True)
    is_featured = models.BooleanField("À la une", default=False)
    views_count = models.PositiveIntegerField("Nombre de vues", default=0)
    helpful_count = models.PositiveIntegerField("Votes utiles", default=0)
    
    # Dates
    author = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Auteur"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_featured', '-created_at']
        verbose_name = "Article"
        verbose_name_plural = "Articles"
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if not self.meta_description:
            self.meta_description = self.summary
        super().save(*args, **kwargs)
    
    def increment_views(self):
        """Incrémenter le compteur de vues."""
        self.views_count += 1
        self.save(update_fields=['views_count'])
    
    def mark_helpful(self):
        """Marquer l'article comme utile."""
        self.helpful_count += 1
        self.save(update_fields=['helpful_count'])


class ArticleTag(models.Model):
    """Tag pour organiser les articles."""
    
    name = models.CharField("Nom", max_length=50, unique=True)
    slug = models.SlugField(unique=True)
    articles = models.ManyToManyField(
        KnowledgeArticle,
        related_name='tags',
        blank=True
    )
    
    class Meta:
        ordering = ['name']
        verbose_name = "Tag"
        verbose_name_plural = "Tags"
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)


class FAQ(models.Model):
    """Questions fréquemment posées."""
    
    AUDIENCE_CHOICES = [
        ('all', 'Tous'),
        ('prospect', 'Prospects'),
        ('client', 'Clients'),
    ]
    
    question = models.CharField("Question", max_length=255)
    answer = models.TextField("Réponse", help_text="Markdown supporté")
    category = models.ForeignKey(
        KnowledgeCategory,
        on_delete=models.CASCADE,
        related_name='faqs',
        verbose_name="Catégorie"
    )
    audience = models.CharField(
        "Audience",
        max_length=20,
        choices=AUDIENCE_CHOICES,
        default='all'
    )
    order = models.PositiveIntegerField("Ordre", default=0)
    is_active = models.BooleanField("Active", default=True)
    views_count = models.PositiveIntegerField("Vues", default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"
    
    def __str__(self):
        return self.question


# ===========================
# E-learning Academy Courses
# ===========================

class AcademyCourse(models.Model):
    """Cours de formation pour les clients."""
    
    LEVEL_CHOICES = [
        ('beginner', '🟢 Débutant'),
        ('intermediate', '🟡 Intermédiaire'),
        ('advanced', '🔴 Avancé'),
    ]
    
    CATEGORY_CHOICES = [
        ('seo', '🔍 SEO'),
        ('content', '📝 Content Marketing'),
        ('email', '📧 Email Marketing'),
        ('social', '📱 Social Media'),
        ('analytics', '📊 Analytics'),
        ('design', '🎨 Design Web'),
        ('conversion', '🎯 Conversion Optimization'),
        ('growth', '📈 Growth Hacking'),
    ]
    
    title = models.CharField("Titre", max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField("Description")
    category = models.CharField("Catégorie", max_length=50, choices=CATEGORY_CHOICES)
    level = models.CharField("Niveau", max_length=20, choices=LEVEL_CHOICES)
    
    # Contenu
    introduction = models.TextField("Introduction")
    learning_objectives = models.JSONField(
        "Objectifs d'apprentissage",
        default=list,
        help_text='["Comprendre les principes SEO", "Optimiser Meta", ...]'
    )
    
    # Durée
    estimated_duration_hours = models.PositiveIntegerField("Durée estimée (h)", default=2)
    
    # Instructeur
    instructor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Statut
    is_published = models.BooleanField("Publié", default=False)
    is_featured = models.BooleanField("À la une", default=False)
    
    # Stats
    students_count = models.PositiveIntegerField("Nombre d'élèves", default=0)
    rating = models.DecimalField("Note moyenne", max_digits=3, decimal_places=2, default=0)
    
    # Dates
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_featured', '-created_at']
        verbose_name = "Cours"
        verbose_name_plural = "Cours"
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class AcademyLesson(models.Model):
    """Leçon d'un cours."""
    
    course = models.ForeignKey(AcademyCourse, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField("Titre", max_length=255)
    order = models.PositiveIntegerField("Ordre", default=0)
    
    # Contenu
    video_url = models.URLField("Lien vidéo", blank=True, help_text="YouTube/Vimeo")
    video_duration_minutes = models.PositiveIntegerField("Durée vidéo (min)", default=0)
    content = models.TextField("Contenu (Markdown)")
    
    # Ressources
    resources = models.JSONField(
        "Ressources",
        default=list,
        help_text='[{"title": "PDF", "url": "..."}, ...]'
    )
    
    # Quiz
    quiz_content = models.JSONField(
        "Quiz",
        default=dict,
        blank=True,
        help_text='{"questions": [{"question": "...", "answers": [...], "correct": 0}]}'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order']
        unique_together = ['course', 'order']
        verbose_name = "Leçon"
        verbose_name_plural = "Leçons"
    
    def __str__(self):
        return f"{self.course.title} - Lesson {self.order}: {self.title}"


class ClientCourseEnrollment(models.Model):
    """Inscription d'un client à un cours."""
    
    STATUS_CHOICES = [
        ('enrolled', 'Inscrit'),
        ('in_progress', 'En cours'),
        ('completed', 'Complété'),
        ('abandoned', 'Abandonné'),
    ]
    
    client = models.ForeignKey(
        'clients.ClientProfile',
        on_delete=models.CASCADE,
        related_name='course_enrollments'
    )
    course = models.ForeignKey(AcademyCourse, on_delete=models.CASCADE)
    
    status = models.CharField("Statut", max_length=20, choices=STATUS_CHOICES, default='enrolled')
    progress_percent = models.PositiveIntegerField("Progression (%)", default=0)
    
    # Certificat
    certificate_earned = models.BooleanField("Certificat obtenu", default=False)
    certificate_url = models.URLField("URL certificat", blank=True)
    
    # Dates
    enrolled_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField("Débuté le", null=True, blank=True)
    completed_at = models.DateTimeField("Complété le", null=True, blank=True)
    
    class Meta:
        unique_together = ['client', 'course']
        ordering = ['-enrolled_at']
        verbose_name = "Inscription cours"
        verbose_name_plural = "Inscriptions cours"
    
    def __str__(self):
        return f"{self.client} - {self.course}"
    
    def complete_course(self):
        """Marquer le cours comme complété."""
        from django.utils import timezone
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.progress_percent = 100
        self.certificate_earned = True
        self.save()


class ClientQuizResult(models.Model):
    """Résultat de quiz."""
    
    enrollment = models.ForeignKey(ClientCourseEnrollment, on_delete=models.CASCADE)
    lesson = models.ForeignKey(AcademyLesson, on_delete=models.CASCADE)
    
    score_percent = models.PositiveIntegerField("Score (%)")
    answers = models.JSONField("Réponses")
    
    completed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['enrollment', 'lesson']
        verbose_name = "Résultat quiz"
        verbose_name_plural = "Résultats quiz"
    
    def __str__(self):
        return f"{self.enrollment.client} - {self.lesson.course.title}: {self.score_percent}%"
