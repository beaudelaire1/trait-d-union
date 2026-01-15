"""Models pour les services proposés par Trait d'Union Studio."""
from decimal import Decimal
from django.db import models
from django.utils.translation import gettext_lazy as _


class ServiceCategory(models.Model):
    """Catégorie de service (ex: Sites web, Applications, Maintenance)."""
    
    name = models.CharField(_("Nom"), max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(_("Description"), blank=True)
    icon = models.CharField(_("Icône"), max_length=50, blank=True, help_text="Nom de l'icône (ex: globe, code, wrench)")
    order = models.PositiveIntegerField(_("Ordre"), default=0)
    
    class Meta:
        ordering = ['order', 'name']
        verbose_name = _("catégorie de service")
        verbose_name_plural = _("catégories de services")
    
    def __str__(self) -> str:
        return self.name


class Service(models.Model):
    """Service proposé par l'agence."""
    
    category = models.ForeignKey(
        ServiceCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='services',
        verbose_name=_("Catégorie")
    )
    name = models.CharField(_("Nom"), max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField(_("Description"))
    short_description = models.CharField(_("Description courte"), max_length=255, blank=True)
    
    # Tarification
    base_price = models.DecimalField(
        _("Prix de base HT"),
        max_digits=10,
        decimal_places=2,
        default=Decimal("0.00")
    )
    price_unit = models.CharField(
        _("Unité de prix"),
        max_length=50,
        default="forfait",
        help_text="Ex: forfait, jour, heure, mois"
    )
    
    # Options
    is_active = models.BooleanField(_("Actif"), default=True)
    is_featured = models.BooleanField(_("Mis en avant"), default=False)
    
    # Métadonnées
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category__order', 'name']
        verbose_name = _("service")
        verbose_name_plural = _("services")
    
    def __str__(self) -> str:
        return self.name
