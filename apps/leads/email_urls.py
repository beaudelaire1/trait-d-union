"""URL configuration for email composition (admin area)."""
from django.urls import path

from .email_views import (
    EmailComposeView, 
    EmailListView, 
    EmailDetailView,
    EmailTemplateAPIView,
    SendEmailView,
)

app_name = 'admin_emails'

urlpatterns = [
    path('', EmailListView.as_view(), name='email_list'),
    path('compose/', EmailComposeView.as_view(), name='email_compose'),
    path('<int:pk>/', EmailDetailView.as_view(), name='email_detail'),
    path('<int:pk>/send/', SendEmailView.as_view(), name='email_send'),
    path('api/templates/<int:pk>/', EmailTemplateAPIView.as_view(), name='template_api'),
]
