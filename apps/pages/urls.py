"""URL configuration for the pages app."""
from django.urls import path

from .views import (
    HomeView, ServicesView, MethodView,
    FAQView, MentionsLegalesView, ConfidentialiteView, CGVView, LegalView,
)


app_name = 'pages'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('services/', ServicesView.as_view(), name='services'),
    path('method/', MethodView.as_view(), name='method'),
    path('faq/', FAQView.as_view(), name='faq'),
    path('mentions-legales/', MentionsLegalesView.as_view(), name='mentions_legales'),
    path('confidentialite/', ConfidentialiteView.as_view(), name='confidentialite'),
    path('cgv/', CGVView.as_view(), name='cgv'),
    path('legal/', LegalView.as_view(), name='legal'),
]