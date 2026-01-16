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
