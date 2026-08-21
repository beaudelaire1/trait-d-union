"""URL configuration for the pages app."""
from django.urls import path

from .p0_views import HomeP0View
from .views import (
    ServicesView, MethodView,
    FAQView, MentionsLegalesView, ConfidentialiteView, CGVView,
)


app_name = 'pages'

urlpatterns = [
    path('', HomeP0View.as_view(), name='home'),
    path('services/', ServicesView.as_view(), name='services'),
    path('method/', MethodView.as_view(), name='method'),
    path('faq/', FAQView.as_view(), name='faq'),
    path('mentions-legales/', MentionsLegalesView.as_view(), name='mentions_legales'),
    path('confidentialite/', ConfidentialiteView.as_view(), name='confidentialite'),
    path('cgv/', CGVView.as_view(), name='cgv'),
    # Alias historique : même source légale afin d'éviter deux vérités publiques.
    path('legal/', MentionsLegalesView.as_view(), name='legal'),
]
