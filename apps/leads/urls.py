"""URL configuration for the leads app."""
from django.urls import path

from .views import ContactView, DynamicFieldsView, ContactSuccessView
from .email_views import (
    EmailComposeView, 
    EmailListView, 
    EmailDetailView,
    EmailTemplateAPIView
)


app_name = 'leads'

urlpatterns = [
    path('', ContactView.as_view(), name='contact'),
    path('fields/', DynamicFieldsView.as_view(), name='dynamic_fields'),
    path('success/', ContactSuccessView.as_view(), name='success'),
    
    # Email composition
    path('emails/', EmailListView.as_view(), name='email_list'),
    path('emails/compose/', EmailComposeView.as_view(), name='email_compose'),
    path('emails/<int:pk>/', EmailDetailView.as_view(), name='email_detail'),
    path('api/templates/<int:pk>/', EmailTemplateAPIView.as_view(), name='template_api'),
]