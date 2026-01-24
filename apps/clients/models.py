"""Client models for the VIP client portal.

This module provides the ClientProfile model which extends the User model
to store client-specific information and preferences.
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class ClientProfile(models.Model):
    """Extended profile for client users."""
    
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='client_profile'
    )
    company_name = models.CharField(
        "Nom de l'entreprise",
        max_length=200,
        blank=True
    )
    phone = models.CharField(
        "Téléphone",
        max_length=20,
        blank=True
    )
    address = models.TextField(
        "Adresse",
        blank=True
    )
    siret = models.CharField(
        "SIRET",
        max_length=14,
        blank=True
    )
    tva_number = models.CharField(
        "N° TVA intracommunautaire",
        max_length=20,
        blank=True
    )
    avatar = models.ImageField(
        "Photo de profil",
        upload_to='clients/avatars/',
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Preferences
    email_notifications = models.BooleanField(
        "Notifications par email",
        default=True
    )
    
    class Meta:
        verbose_name = "Profil client"
        verbose_name_plural = "Profils clients"
    
    def __str__(self):
        if self.company_name:
            return f"{self.company_name} ({self.user.email})"
        return self.user.email
    
    @property
    def full_name(self):
        """Return full name or company name."""
        if self.user.get_full_name():
            return self.user.get_full_name()
        return self.company_name or self.user.username


class ClientNotification(models.Model):
    """Notification for client portal."""
    
    NOTIFICATION_TYPES = [
        ('quote', 'Nouveau devis'),
        ('invoice', 'Nouvelle facture'),
        ('project', 'Mise à jour projet'),
        ('document', 'Nouveau document'),
        ('message', 'Message'),
    ]
    
    client = models.ForeignKey(
        ClientProfile,
        on_delete=models.CASCADE,
        related_name='notifications',
        verbose_name="Client"
    )
    notification_type = models.CharField(
        "Type",
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default='message'
    )
    title = models.CharField(
        "Titre",
        max_length=200
    )
    message = models.TextField(
        "Message"
    )
    related_url = models.CharField(
        "URL associée",
        max_length=255,
        blank=True
    )
    read = models.BooleanField(
        "Lu",
        default=False
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Notification"
        verbose_name_plural = "Notifications"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.client}"
    
    @property
    def type(self):
        """Alias for notification_type for template compatibility."""
        return self.notification_type


class ProjectStatus(models.TextChoices):
    """Project status choices."""
    BRIEFING = 'briefing', '📋 Cadrage'
    DESIGN = 'design', '🎨 Design'
    DEVELOPMENT = 'development', '💻 Développement'
    REVIEW = 'review', '🔍 Recette'
    DELIVERED = 'delivered', '✅ Livré'
    MAINTENANCE = 'maintenance', '🔧 Maintenance'


class Project(models.Model):
    """Client project for tracking progress."""
    
    client = models.ForeignKey(
        ClientProfile,
        on_delete=models.CASCADE,
        related_name='projects',
        verbose_name="Client"
    )
    name = models.CharField(
        "Nom du projet",
        max_length=200
    )
    description = models.TextField(
        "Description",
        blank=True
    )
    status = models.CharField(
        "Statut",
        max_length=20,
        choices=ProjectStatus.choices,
        default=ProjectStatus.BRIEFING
    )
    progress = models.PositiveIntegerField(
        "Progression (%)",
        default=0
    )
    start_date = models.DateField(
        "Date de début",
        null=True,
        blank=True
    )
    estimated_delivery = models.DateField(
        "Livraison estimée",
        null=True,
        blank=True
    )
    delivered_at = models.DateField(
        "Date de livraison",
        null=True,
        blank=True
    )
    
    # Linked documents
    quote = models.ForeignKey(
        'devis.Quote',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='projects',
        verbose_name="Devis associé"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Projet"
        verbose_name_plural = "Projets"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.name} - {self.client}"
    
    def get_status_display_with_emoji(self):
        """Return status with emoji."""
        return self.get_status_display()
    
    @property
    def is_active(self):
        """Check if project is active (not delivered)."""
        return self.status not in [ProjectStatus.DELIVERED, ProjectStatus.MAINTENANCE]


class ProjectMilestone(models.Model):
    """Milestone/checkpoint for a project."""
    
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='milestones',
        verbose_name="Projet"
    )
    title = models.CharField(
        "Titre",
        max_length=200
    )
    description = models.TextField(
        "Description",
        blank=True
    )
    status = models.CharField(
        "Statut",
        max_length=20,
        choices=[
            ('pending', '⏳ En attente'),
            ('in_progress', '🔄 En cours'),
            ('completed', '✅ Terminé'),
        ],
        default='pending'
    )
    due_date = models.DateField(
        "Échéance",
        null=True,
        blank=True
    )
    completed_at = models.DateTimeField(
        "Terminé le",
        null=True,
        blank=True
    )
    order = models.PositiveIntegerField(
        "Ordre",
        default=0
    )
    
    class Meta:
        verbose_name = "Jalon"
        verbose_name_plural = "Jalons"
        ordering = ['order', 'due_date']
    
    def __str__(self):
        return f"{self.project.name} - {self.title}"
    
    def mark_completed(self):
        """Mark milestone as completed."""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()


class ProjectActivity(models.Model):
    """Activity log for project transparency - tracks all changes."""
    
    ACTIVITY_TYPES = [
        ('status_change', '🔄 Changement de statut'),
        ('progress_update', '📊 Mise à jour progression'),
        ('milestone_completed', '✅ Jalon terminé'),
        ('document_added', '📄 Document ajouté'),
        ('comment_added', '💬 Commentaire'),
        ('delivery', '🚀 Livraison'),
        ('feedback', '📝 Retour client'),
        ('meeting', '📅 Réunion'),
    ]
    
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='activities',
        verbose_name="Projet"
    )
    activity_type = models.CharField(
        "Type d'activité",
        max_length=30,
        choices=ACTIVITY_TYPES
    )
    title = models.CharField(
        "Titre",
        max_length=200
    )
    description = models.TextField(
        "Description",
        blank=True
    )
    # Track who made the action
    performed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='project_activities',
        verbose_name="Effectué par"
    )
    is_client_visible = models.BooleanField(
        "Visible par le client",
        default=True
    )
    # Optional: link to related milestone
    milestone = models.ForeignKey(
        'ProjectMilestone',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='activities',
        verbose_name="Jalon associé"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Activité projet"
        verbose_name_plural = "Activités projet"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.project.name} - {self.title}"
    
    @property
    def icon(self):
        """Return emoji for activity type."""
        icons = {
            'status_change': '🔄',
            'progress_update': '📊',
            'milestone_completed': '✅',
            'document_added': '📄',
            'comment_added': '💬',
            'delivery': '🚀',
            'feedback': '📝',
            'meeting': '📅',
        }
        return icons.get(self.activity_type, '📌')


class ProjectComment(models.Model):
    """Comments/messages on a project for client-team communication."""
    
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name="Projet"
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='project_comments',
        verbose_name="Auteur"
    )
    message = models.TextField(
        "Message"
    )
    # Optional: attach to a specific milestone
    milestone = models.ForeignKey(
        'ProjectMilestone',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='comments',
        verbose_name="Jalon associé"
    )
    # For file attachments
    attachment = models.FileField(
        "Pièce jointe",
        upload_to='projects/comments/%Y/%m/',
        blank=True,
        null=True
    )
    is_internal = models.BooleanField(
        "Note interne (invisible client)",
        default=False
    )
    read_by_client = models.BooleanField(
        "Lu par le client",
        default=False
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Commentaire projet"
        verbose_name_plural = "Commentaires projet"
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.project.name} - {self.author.get_full_name()}"
    
    @property
    def is_from_client(self):
        """Check if comment is from the client."""
        return hasattr(self.author, 'client_profile')


class ClientDocument(models.Model):
    """Document uploaded by or for the client."""
    
    DOCUMENT_TYPES = [
        ('brief', '📄 Cahier des charges'),
        ('logo', '🎨 Logo'),
        ('asset', '📦 Asset'),
        ('contract', '📝 Contrat'),
        ('other', '📎 Autre'),
    ]
    
    client = models.ForeignKey(
        ClientProfile,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name="Client"
    )
    project = models.ForeignKey(
        Project,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='documents',
        verbose_name="Projet"
    )
    title = models.CharField(
        "Titre",
        max_length=200
    )
    document_type = models.CharField(
        "Type",
        max_length=20,
        choices=DOCUMENT_TYPES,
        default='other'
    )
    file = models.FileField(
        "Fichier",
        upload_to='clients/documents/%Y/%m/'
    )
    uploaded_by_client = models.BooleanField(
        "Uploadé par le client",
        default=False
    )
    notes = models.TextField(
        "Notes",
        blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.client}"
    
    @property
    def file_extension(self):
        """Return file extension."""
        return self.file.name.split('.')[-1].lower() if self.file else ''
    
    @property
    def is_image(self):
        """Check if file is an image."""
        return self.file_extension in ['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg']
