"""URL configuration for the simulateur app."""
from django.urls import path

from .views import SimulateurView

app_name = 'simulateur'

urlpatterns = [
    path('', SimulateurView.as_view(), name='simulateur'),
]
