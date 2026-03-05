"""Models for the pages app."""
from django.db import models
from datetime import timedelta
from django.utils import timezone


class Testimonial(models.Model):
    """Client testimonial for the home page."""
    
    client_name = models.CharField("Nom du client", max_length=200)
    company_name = models.CharField("Nom de l'entreprise", max_length=200, blank=True)
    position = models.CharField("Poste", max_length=100, blank=True)
    content = models.TextField("Témoignage")
    avatar = models.ImageField("Photo", upload_to='testimonials/', blank=True, null=True)
    rating = models.PositiveSmallIntegerField("Note", default=5, help_text="Note sur 5")
    
    is_published = models.BooleanField("Publié", default=True)
    order = models.PositiveIntegerField("Ordre d'affichage", default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = "Témoignage"
        verbose_name_plural = "Témoignages"
    
    def __str__(self) -> str:
        return f"{self.client_name} - {self.company_name or 'Particulier'}"


class SimulatorQuotaUsage(models.Model):
    """Track simulator PDF generations by IP address + User-Agent (for rate limiting).
    
    Non-authenticated users are limited to 5 PDF generations per 24 hours per IP+UA combo.
    """
    ip_address = models.GenericIPAddressField("Adresse IP")
    user_agent = models.TextField("User-Agent", db_index=False)
    user_agent_hash = models.CharField("Hash User-Agent", max_length=64, db_index=True, 
                                        help_text="SHA256 hash for indexing (IP+UA is the unique key)")
    generation_count = models.PositiveIntegerField("Nombre de générations", default=1)
    last_generation = models.DateTimeField("Dernière génération", auto_now=True)
    created_at = models.DateTimeField("Créé", auto_now_add=True)
    
    class Meta:
        verbose_name = "Utilisation quota simulateur"
        verbose_name_plural = "Utilisations quota simulateur"
        indexes = [
            models.Index(fields=['ip_address', 'user_agent_hash']),
            models.Index(fields=['last_generation']),
        ]
    
    def __str__(self) -> str:
        return f"{self.ip_address} - {self.user_agent[:50]}... ({self.generation_count} gens)"
    
    @classmethod
    def get_or_create_for_request(cls, request):
        """Get or create record for this IP + User-Agent combo."""
        import hashlib
        ip = cls.get_client_ip(request)
        ua = request.META.get('HTTP_USER_AGENT', '')
        ua_hash = hashlib.sha256(ua.encode()).hexdigest()
        record, created = cls.objects.get_or_create(
            ip_address=ip,
            user_agent_hash=ua_hash,
            defaults={'user_agent': ua}
        )
        return record
    
    @staticmethod
    def get_client_ip(request):
        """Extract client IP, respecting X-Forwarded-For (proxy-safe)."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')
    
    def is_quota_exceeded(self, quota=5, window_hours=24):
        """Check if quota exceeded within the time window."""
        cutoff = timezone.now() - timedelta(hours=window_hours)
        return self.generation_count >= quota and self.last_generation > cutoff
    
    def increment_and_save(self):
        """Increment counter and save."""
        self.generation_count += 1
        self.save(update_fields=['generation_count', 'last_generation'])
    """Client testimonial for the home page."""
    
    client_name = models.CharField("Nom du client", max_length=200)
    company_name = models.CharField("Nom de l'entreprise", max_length=200, blank=True)
    position = models.CharField("Poste", max_length=100, blank=True)
    content = models.TextField("Témoignage")
    avatar = models.ImageField("Photo", upload_to='testimonials/', blank=True, null=True)
    rating = models.PositiveSmallIntegerField("Note", default=5, help_text="Note sur 5")
    
    is_published = models.BooleanField("Publié", default=True)
    order = models.PositiveIntegerField("Ordre d'affichage", default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = "Témoignage"
        verbose_name_plural = "Témoignages"
    
    def __str__(self) -> str:
        return f"{self.client_name} - {self.company_name or 'Particulier'}"
