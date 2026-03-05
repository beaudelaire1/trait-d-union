"""Models for the pages app."""
from django.db import models


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
