"""Dashboard URLs for admin cockpit.

All views wrapped with staff_member_required at URL level.
"""
from django.contrib.admin.views.decorators import staff_member_required
from django.urls import path

from . import dashboard_views

app_name = 'dashboard'

urlpatterns = [
    path('', staff_member_required(dashboard_views.dashboard_view), name='index'),
]
