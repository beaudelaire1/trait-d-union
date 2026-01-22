from django.db import models
from django.utils import timezone
from django.conf import settings

class Prospect(models.Model):
    STATUS_CHOICES = [
        ('new', 'Nouveau'),
        ('contacted', 'Contacté'),
        ('responded', 'A répondu'),
        ('converted', 'Converti'),
        ('archived', 'Archivé')
    ]
    
    email = models.EmailField(unique=True)
    contact_name = models.CharField(max_length=255, blank=True)
    company_name = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    website = models.URLField(blank=True)
    sector = models.CharField(max_length=100, blank=True)
    source = models.CharField(max_length=50, default='cold_email')
    
    # Qualification info
    activity_description = models.TextField(blank=True)
    pain_points = models.TextField(blank=True)
    priority = models.IntegerField(default=1)
    notes = models.TextField(blank=True)
    tags = models.CharField(max_length=255, blank=True, help_text="Comma separated tags")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new')
    next_follow_up = models.DateTimeField(null=True, blank=True)
    last_contacted_at = models.DateTimeField(null=True, blank=True) # Added field
    converted_to_client = models.BooleanField(default=False) # Added field
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.email

class EmailTemplate(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    subject = models.CharField(max_length=255)
    html_template = models.TextField(help_text="HTML content")
    text_content = models.TextField(blank=True, help_text="Plain text version")
    category = models.CharField(max_length=50, default='general')
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

class ProspectMessage(models.Model):
    DIRECTION_CHOICES = [
        ('inbound', 'Reçu'),
        ('outbound', 'Envoyé')
    ]
    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('sent', 'Envoyé'),
        ('delivered', 'Reçu'),
        ('opened', 'Ouvert'),
        ('clicked', 'Cliqué'),
        ('failed', 'Échoué')
    ]
    
    prospect = models.ForeignKey(Prospect, on_delete=models.CASCADE, related_name='messages')
    subject = models.CharField(max_length=255)
    content = models.TextField()
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES, default='outbound')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='sent')
    message_id = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.direction} - {self.prospect.email}"

class ProspectActivity(models.Model):
    prospect = models.ForeignKey(Prospect, on_delete=models.CASCADE, related_name='activities')
    activity_type = models.CharField(max_length=50)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

class EmailCampaign(models.Model):
    name = models.CharField(max_length=255)
    template = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    subject = models.CharField(max_length=255, blank=True) # Override template subject
    content = models.TextField(blank=True) # Override template content
    status = models.CharField(max_length=20, default='draft')
    
    # Scheduling
    scheduled_at = models.DateTimeField(null=True, blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    
    # Stats
    total_sent = models.IntegerField(default=0)
    total_opened = models.IntegerField(default=0)
    total_clicked = models.IntegerField(default=0)
    total_replied = models.IntegerField(default=0)
    
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name

    @property
    def open_rate(self):
        if self.total_sent > 0:
            return round((self.total_opened / self.total_sent) * 100, 1)
        return 0

    @property
    def click_rate(self):
        if self.total_sent > 0:
            return round((self.total_clicked / self.total_sent) * 100, 1)
        return 0

class CampaignRecipient(models.Model):
    campaign = models.ForeignKey(EmailCampaign, on_delete=models.CASCADE, related_name='recipients')
    prospect = models.ForeignKey(Prospect, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default='pending')
    sent_at = models.DateTimeField(null=True, blank=True)
    opened_at = models.DateTimeField(null=True, blank=True)
    clicked_at = models.DateTimeField(null=True, blank=True)
    replied_at = models.DateTimeField(null=True, blank=True)
