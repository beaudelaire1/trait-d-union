"""URL configuration for the pages app."""
from django.urls import path

from .views import HomeView, ServicesView, MethodView, LegalView


app_name = 'pages'

urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('services/', ServicesView.as_view(), name='services'),
    path('method/', MethodView.as_view(), name='method'),
    path('legal/', LegalView.as_view(), name='legal'),
]