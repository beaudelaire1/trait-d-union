"""URL configuration for the pages app."""
from django.urls import path
from django.views.generic import TemplateView

from .views import HomeView, ServicesView, MethodView


app_name = 'pages'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('services/', ServicesView.as_view(), name='services'),
    path('method/', MethodView.as_view(), name='method'),
    path('mentions-legales/', TemplateView.as_view(template_name='pages/mentions_legales.html'), name='mentions_legales'),
    path('confidentialite/', TemplateView.as_view(template_name='pages/confidentialite.html'), name='confidentialite'),
    path('cgv/', TemplateView.as_view(template_name='pages/cgv.html'), name='cgv'),
    path('legal/', TemplateView.as_view(template_name='pages/legal.html'), name='legal'),
]