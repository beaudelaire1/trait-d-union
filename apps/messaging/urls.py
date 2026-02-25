"""Messaging URLs — all views require staff access.

Protection is enforced at URL level via staff_member_required wrapper,
in addition to any view-level decorators.
"""
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import path

from . import views


def _s(view_func):
    """Wrap a FBV with staff_member_required at URL level."""
    return staff_member_required(view_func)


app_name = 'messaging'

urlpatterns = [
    # Dashboard / Inbox
    path('', _s(views.inbox), name='inbox'),
    path('compose/', _s(views.compose), name='compose'),

    # Prospects
    path('prospects/', _s(views.prospect_list), name='prospect_list'),
    path('prospects/create/', _s(views.prospect_create), name='prospect_create'),
    path('prospects/import/', _s(views.import_prospects), name='import_prospects'),
    path('prospects/<int:pk>/', _s(views.prospect_detail), name='prospect_detail'),
    path('prospects/<int:pk>/edit/', _s(views.prospect_edit), name='prospect_edit'),
    path('prospects/<int:pk>/send/', _s(views.send_prospect_email_view), name='send_prospect_email'),
    path('prospects/<int:pk>/quick-send/', _s(views.quick_send_email), name='quick_send_email'),

    # Campaigns
    path('campaigns/', _s(views.campaign_list), name='campaign_list'),
    path('campaigns/create/', _s(views.campaign_create), name='campaign_create'),
    path('campaigns/<int:pk>/', _s(views.campaign_detail), name='campaign_detail'),

    # Templates
    path('templates/', _s(views.template_list), name='template_list'),

    # API endpoints
    path('api/send/', _s(views.send_email_api), name='api_send_email'),
    path('api/prospects/quick-add/', _s(views.quick_add_prospect), name='quick_add_prospect'),
]
