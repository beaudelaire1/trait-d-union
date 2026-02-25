"""URL configuration for email composition (admin area).

All views are wrapped with staff_member_required at URL level
to enforce authentication even if a view forgets the decorator.
"""
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import path

from .email_views import (
    EmailComposeView, 
    EmailListView, 
    EmailDetailView,
    EmailTemplateAPIView,
    SendEmailView,
    BulkEmailView,
)


def _staff(view_class):
    """Wrap a CBV with staff_member_required at URL level."""
    return staff_member_required(view_class.as_view())


app_name = 'admin_emails'

urlpatterns = [
    path('', _staff(EmailListView), name='email_list'),
    path('compose/', _staff(EmailComposeView), name='email_compose'),
    path('bulk/', _staff(BulkEmailView), name='bulk_email'),
    path('<int:pk>/', _staff(EmailDetailView), name='email_detail'),
    path('<int:pk>/send/', _staff(SendEmailView), name='email_send'),
    path('api/templates/<int:pk>/', _staff(EmailTemplateAPIView), name='template_api'),
]
