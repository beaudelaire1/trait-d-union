"""Views for the client portal."""
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, DetailView, UpdateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse

from .models import ClientProfile, Project, ProjectMilestone, ClientDocument
from .forms import ClientProfileForm, DocumentUploadForm


class ClientRequiredMixin(LoginRequiredMixin):
    """Mixin to ensure user has a client profile."""
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            # Create profile if doesn't exist
            ClientProfile.objects.get_or_create(user=request.user)
        return super().dispatch(request, *args, **kwargs)


class DashboardView(ClientRequiredMixin, TemplateView):
    """Client dashboard with overview of projects and documents."""
    template_name = 'clients/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.request.user.client_profile
        
        # Active projects
        context['active_projects'] = profile.projects.filter(
            status__in=['briefing', 'design', 'development', 'review']
        )[:5]
        
        # Recent documents
        context['recent_documents'] = profile.documents.all()[:5]
        
        # Stats
        context['stats'] = {
            'total_projects': profile.projects.count(),
            'active_projects': profile.projects.exclude(status='delivered').count(),
            'documents': profile.documents.count(),
        }
        
        # Get quotes and invoices linked to client email
        from apps.devis.models import Quote
        from apps.factures.models import Invoice
        
        context['recent_quotes'] = Quote.objects.filter(
            client__email=self.request.user.email
        ).order_by('-created_at')[:5]
        
        context['recent_invoices'] = Invoice.objects.filter(
            quote__client__email=self.request.user.email
        ).order_by('-created_at')[:5]
        
        return context


class ProfileView(ClientRequiredMixin, UpdateView):
    """View and edit client profile."""
    model = ClientProfile
    form_class = ClientProfileForm
    template_name = 'clients/profile.html'
    success_url = reverse_lazy('clients:profile')
    
    def get_object(self, queryset=None):
        return self.request.user.client_profile
    
    def form_valid(self, form):
        messages.success(self.request, 'Profil mis à jour avec succès.')
        return super().form_valid(form)


class ProjectListView(ClientRequiredMixin, ListView):
    """List all client projects."""
    model = Project
    template_name = 'clients/project_list.html'
    context_object_name = 'projects'
    
    def get_queryset(self):
        return self.request.user.client_profile.projects.all()


class ProjectDetailView(ClientRequiredMixin, DetailView):
    """Detail view for a project with timeline."""
    model = Project
    template_name = 'clients/project_detail.html'
    context_object_name = 'project'
    
    def get_queryset(self):
        return self.request.user.client_profile.projects.all()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['milestones'] = self.object.milestones.all()
        context['documents'] = self.object.documents.all()
        
        # Timeline stages
        context['stages'] = [
            {'id': 'briefing', 'label': 'Cadrage', 'icon': '📋'},
            {'id': 'design', 'label': 'Design', 'icon': '🎨'},
            {'id': 'development', 'label': 'Développement', 'icon': '💻'},
            {'id': 'review', 'label': 'Recette', 'icon': '🔍'},
            {'id': 'delivered', 'label': 'Livré', 'icon': '✅'},
        ]
        
        return context


class DocumentListView(ClientRequiredMixin, ListView):
    """List all client documents."""
    model = ClientDocument
    template_name = 'clients/document_list.html'
    context_object_name = 'documents'
    
    def get_queryset(self):
        return self.request.user.client_profile.documents.all()


@login_required
def upload_document(request, project_id=None):
    """Upload a document."""
    profile = request.user.client_profile
    project = None
    
    if project_id:
        project = get_object_or_404(Project, id=project_id, client=profile)
    
    if request.method == 'POST':
        form = DocumentUploadForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.client = profile
            document.project = project
            document.uploaded_by_client = True
            document.save()
            messages.success(request, 'Document uploadé avec succès.')
            
            if request.headers.get('HX-Request'):
                return render(request, 'clients/partials/document_card.html', {
                    'document': document
                })
            
            if project:
                return redirect('clients:project_detail', pk=project.pk)
            return redirect('clients:documents')
    else:
        form = DocumentUploadForm()
    
    return render(request, 'clients/upload_document.html', {
        'form': form,
        'project': project
    })


class QuoteListView(ClientRequiredMixin, ListView):
    """List all quotes for the client."""
    template_name = 'clients/quote_list.html'
    context_object_name = 'quotes'
    
    def get_queryset(self):
        from apps.devis.models import Quote
        return Quote.objects.filter(
            client__email=self.request.user.email
        ).order_by('-created_at')


class InvoiceListView(ClientRequiredMixin, ListView):
    """List all invoices for the client."""
    template_name = 'clients/invoice_list.html'
    context_object_name = 'invoices'
    
    def get_queryset(self):
        from apps.factures.models import Invoice
        return Invoice.objects.filter(
            quote__client__email=self.request.user.email
        ).order_by('-created_at')
