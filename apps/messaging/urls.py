from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    # Dashboard / Inbox
    path('', views.inbox, name='inbox'),
    path('compose/', views.compose, name='compose'),
    
    # Prospects
    path('prospects/', views.prospect_list, name='prospect_list'),
    path('prospects/create/', views.prospect_create, name='prospect_create'),
    path('prospects/import/', views.import_prospects, name='import_prospects'),
    path('prospects/<int:pk>/', views.prospect_detail, name='prospect_detail'),
    path('prospects/<int:pk>/edit/', views.prospect_edit, name='prospect_edit'),
    path('prospects/<int:pk>/send/', views.send_prospect_email_view, name='send_prospect_email'),
    path('prospects/<int:pk>/quick-send/', views.quick_send_email, name='quick_send_email'),
    
    # Campaigns
    path('campaigns/', views.campaign_list, name='campaign_list'),
    path('campaigns/create/', views.campaign_create, name='campaign_create'),
    path('campaigns/<int:pk>/', views.campaign_detail, name='campaign_detail'),
    
    # Templates
    path('templates/', views.template_list, name='template_list'),
    
    # API endpoints
    path('api/send/', views.send_email_api, name='api_send_email'),
    path('api/prospects/quick-add/', views.quick_add_prospect, name='quick_add_prospect'),
]
