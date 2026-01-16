"""URL configuration for the client portal."""
from django.urls import path
from . import views

app_name = 'clients'

urlpatterns = [
    # Dashboard
    path('', views.DashboardView.as_view(), name='dashboard'),
    
    # Profile
    path('profil/', views.ProfileView.as_view(), name='profile'),
    
    # Projects
    path('projets/', views.ProjectListView.as_view(), name='projects'),
    path('projets/<int:pk>/', views.ProjectDetailView.as_view(), name='project_detail'),
    
    # Documents
    path('documents/', views.DocumentListView.as_view(), name='documents'),
    path('documents/upload/', views.upload_document, name='upload_document'),
    path('documents/upload/<int:project_id>/', views.upload_document, name='upload_document_project'),
    
    # Quotes & Invoices
    path('devis/', views.QuoteListView.as_view(), name='quotes'),
    path('factures/', views.InvoiceListView.as_view(), name='invoices'),
]
