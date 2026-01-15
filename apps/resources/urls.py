"""URL configuration for the resources app."""
from django.urls import path

from .views import ResourcesView, DownloadView


app_name = 'resources'

urlpatterns = [
    path('', ResourcesView.as_view(), name='list'),
    path('<str:filename>/', DownloadView.as_view(), name='download'),
]