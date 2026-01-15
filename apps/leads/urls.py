"""URL configuration for the leads app."""
from django.urls import path

from .views import ContactView, DynamicFieldsView, ContactSuccessView


app_name = 'leads'

urlpatterns = [
    path('', ContactView.as_view(), name='contact'),
    path('fields/', DynamicFieldsView.as_view(), name='dynamic_fields'),
    path('success/', ContactSuccessView.as_view(), name='success'),
]