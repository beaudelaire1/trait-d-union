"""Views for the client portal."""
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import TemplateView, ListView, DetailView, UpdateView, CreateView
from django.contrib import messages
from django.urls import reverse_lazy
from django.http import JsonResponse, FileResponse
from django.core.files.storage import default_storage
from django.views.decorators.clickjacking import xframe_options_sameorigin

from .models import ClientProfile, Project, ProjectMilestone, ClientDocument, ClientNotification
from .forms import ClientProfileForm, DocumentUploadForm, ClientRequestForm


class ClientRequiredMixin(LoginRequiredMixin):
    """Mixin to ensure user has a client profile."""
    
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            # Create profile if doesn't exist
            ClientProfile.objects.get_or_create(user=request.user)
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        """Add common client context (notifications, badges)."""
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            profile = self.request.user.client_profile
            
            # Notifications non lues
            context['notifications'] = ClientNotification.objects.filter(
                client=profile,
                read=False
            ).order_by('-created_at')[:10]
            context['notifications_count'] = context['notifications'].count()
            
            # Badges pour le menu
            from apps.devis.models import Quote
            from apps.factures.models import Invoice
            
            context['pending_quotes_count'] = Quote.objects.filter(
                client__email=self.request.user.email,
                status='sent'
            ).count()
            
            context['pending_invoices_count'] = Invoice.objects.filter(
                quote__client__email=self.request.user.email,
                status__in=['sent', 'overdue']
            ).count()
        
        return context


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
        milestones = list(self.object.milestones.all())
        context['milestones'] = milestones
        context['documents'] = self.object.documents.all()
        
        # Activity log (visible to client only)
        context['activities'] = self.object.activities.filter(
            is_client_visible=True
        ).select_related('performed_by', 'milestone')[:20]
        
        # Comments (exclude internal notes)
        context['comments'] = self.object.comments.filter(
            is_internal=False
        ).select_related('author', 'milestone')
        
        # Mark unread comments as read
        self.object.comments.filter(
            is_internal=False,
            read_by_client=False
        ).exclude(
            author=self.request.user
        ).update(read_by_client=True)
        
        # Timeline stages
        context['stages'] = [
            {'id': 'briefing', 'label': 'Cadrage', 'icon': '📋'},
            {'id': 'design', 'label': 'Design', 'icon': '🎨'},
            {'id': 'development', 'label': 'Développement', 'icon': '💻'},
            {'id': 'review', 'label': 'Recette', 'icon': '🔍'},
            {'id': 'delivered', 'label': 'Livré', 'icon': '✅'},
        ]
        
        # Calculate completed stages for progress bar
        status_order = ['briefing', 'design', 'development', 'review', 'delivered']
        current_index = status_order.index(self.object.status) if self.object.status in status_order else 0
        context['completed_stages'] = status_order[:current_index]
        
        # === BARRE DE PROGRESSION DYNAMIQUE ===
        total_milestones = len(milestones)
        if total_milestones > 0:
            completed_count = sum(1 for m in milestones if m.status == 'completed')
            in_progress_idx = next(
                (i for i, m in enumerate(milestones) if m.status == 'in_progress'),
                None
            )
            
            # Étape courante (en cours ou prochaine à faire)
            if in_progress_idx is not None:
                current_step = in_progress_idx + 1
                current_milestone = milestones[in_progress_idx]
            elif completed_count < total_milestones:
                # Première étape pending
                pending_idx = next(
                    (i for i, m in enumerate(milestones) if m.status == 'pending'),
                    completed_count
                )
                current_step = pending_idx + 1
                current_milestone = milestones[pending_idx] if pending_idx < total_milestones else None
            else:
                current_step = total_milestones
                current_milestone = milestones[-1] if milestones else None
            
            # Pourcentage de progression
            progress_percent = int((completed_count / total_milestones) * 100)
            if in_progress_idx is not None:
                # Ajouter 50% de l'étape en cours
                progress_percent = int(((completed_count + 0.5) / total_milestones) * 100)
            
            context['milestone_progress'] = {
                'total': total_milestones,
                'completed': completed_count,
                'current_step': current_step,
                'current_milestone': current_milestone,
                'percent': min(progress_percent, 100),
            }
        else:
            context['milestone_progress'] = None
        
        # === CALCUL DÉLAI PROJET ===
        from datetime import date
        project = self.object
        if project.start_date and project.estimated_delivery:
            total_days = (project.estimated_delivery - project.start_date).days
            elapsed_days = (date.today() - project.start_date).days
            remaining_days = (project.estimated_delivery - date.today()).days
            
            # Semaines
            total_weeks = max(1, total_days // 7)
            elapsed_weeks = max(0, elapsed_days // 7)
            remaining_weeks = max(0, remaining_days // 7)
            
            # Pourcentage temps écoulé
            time_percent = min(100, max(0, int((elapsed_days / total_days) * 100))) if total_days > 0 else 0
            
            context['project_timeline'] = {
                'total_weeks': total_weeks,
                'elapsed_weeks': elapsed_weeks,
                'remaining_weeks': remaining_weeks,
                'remaining_days': remaining_days,
                'time_percent': time_percent,
                'is_overdue': remaining_days < 0,
            }
        else:
            context['project_timeline'] = None
        
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


class NewClientRequestView(ClientRequiredMixin, TemplateView):
    """Simplified request form for existing clients.
    
    Unlike the public contact form, this pre-fills client information
    and provides a streamlined experience for repeat customers.
    """
    template_name = 'clients/new_request.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = self.request.user.client_profile
        
        # Pre-fill form with client data
        context['client_data'] = {
            'name': self.request.user.get_full_name() or self.request.user.username,
            'email': self.request.user.email,
            'phone': profile.phone,
            'company': profile.company_name,
            'address': profile.address,
        }
        
        # Get previous projects for context
        context['previous_projects'] = profile.projects.all()[:5]
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle new request submission."""
        from apps.devis.models import QuoteRequest
        
        profile = request.user.client_profile
        
        # Create quote request with pre-filled client data
        quote_request = QuoteRequest.objects.create(
            client_name=request.user.get_full_name() or request.user.username,
            email=request.user.email,
            phone=profile.phone or request.POST.get('phone', ''),
            address=profile.address or request.POST.get('address', ''),
            message=request.POST.get('message', ''),
            preferred_date=request.POST.get('preferred_date') or None,
        )
        
        # Create notification for admin
        messages.success(
            request, 
            'Votre demande a été envoyée avec succès ! Notre équipe vous recontactera sous 24h.'
        )
        
        return redirect('clients:dashboard')


@login_required
def mark_notifications_read(request):
    """Mark all notifications as read for the current user."""
    if request.method == 'POST':
        profile = request.user.client_profile
        ClientNotification.objects.filter(client=profile, read=False).update(read=True)
        return JsonResponse({'success': True})
    return JsonResponse({'error': 'Method not allowed'}, status=405)


@login_required
def add_project_comment(request, project_id):
    """Add a comment to a project (HTMX endpoint)."""
    from .models import ProjectComment, ProjectActivity
    
    profile = request.user.client_profile
    project = get_object_or_404(Project, id=project_id, client=profile)
    
    if request.method == 'POST':
        message = request.POST.get('message', '').strip()
        attachment = request.FILES.get('attachment')
        
        if message or attachment:
            comment = ProjectComment.objects.create(
                project=project,
                author=request.user,
                message=message,
                attachment=attachment,
                is_internal=False  # Client comments are never internal
            )
            
            # Log activity
            ProjectActivity.objects.create(
                project=project,
                activity_type='comment_added',
                title=f"Commentaire de {request.user.get_full_name() or request.user.username}",
                description=message[:100] + '...' if len(message) > 100 else message,
                performed_by=request.user,
                is_client_visible=True
            )
            
            # Return partial for HTMX
            if request.headers.get('HX-Request'):
                return render(request, 'clients/partials/comment_item.html', {
                    'comment': comment,
                    'user': request.user
                })
            
            messages.success(request, 'Commentaire ajouté avec succès.')
            return redirect('clients:project_detail', pk=project.pk)
    
    return redirect('clients:project_detail', pk=project.pk)


@login_required
def quick_request(request):
    """Handle quick requests from client dashboard (HTMX endpoint).
    
    This replaces the need for clients to fill the full public contact form.
    All client data is automatically attached from their profile.
    """
    from apps.leads.models import Lead
    
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    profile = request.user.client_profile
    request_type = request.POST.get('request_type', 'other')
    message = request.POST.get('message', '').strip()
    project_id = request.POST.get('project_id')
    document_ref = request.POST.get('document_ref', '').strip()
    
    # Map request types to lead subjects
    type_labels = {
        'quote': '📄 Demande de devis',
        'invoice': '🧾 Demande de facture',
        'support': '🔧 Support technique',
        'duplicate': '📋 Duplicata de document',
        'other': '💬 Autre demande',
    }
    
    request_label = type_labels.get(request_type, 'Demande client')
    
    # Build the full message with context
    full_message = f"[CLIENT EXISTANT - {request_label}]\n"
    full_message += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
    full_message += f"Client : {request.user.get_full_name() or request.user.username}\n"
    full_message += f"Email : {request.user.email}\n"
    if profile.phone:
        full_message += f"Téléphone : {profile.phone}\n"
    if profile.company_name:
        full_message += f"Entreprise : {profile.company_name}\n"
    full_message += f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    
    if project_id:
        try:
            project = Project.objects.get(id=project_id, client=profile)
            full_message += f"📁 Projet concerné : {project.name}\n\n"
        except Project.DoesNotExist:
            pass
    
    if document_ref:
        full_message += f"📄 Référence document : {document_ref}\n\n"
    
    full_message += f"Message :\n{message}"
    
    # Map request type to project type for Lead model
    project_type_map = {
        'quote': 'vitrine',  # Default, admin will understand from message
        'invoice': 'vitrine',
        'support': 'plateforme',
        'duplicate': 'vitrine',
        'other': 'vitrine',
    }
    
    # Create the lead (will trigger admin notification)
    lead = Lead.objects.create(
        name=f"[CLIENT] {request.user.get_full_name() or request.user.username}",
        email=request.user.email,
        project_type=project_type_map.get(request_type, 'vitrine'),
        message=full_message,
    )
    
    # Create notification for the client
    ClientNotification.objects.create(
        client=profile,
        notification_type='message',
        title=f"Demande envoyée : {request_label}",
        message=f"Votre demande a été transmise à l'équipe. Réponse sous 24h.",
        related_url='',
    )
    
    # Return success HTML for HTMX
    if request.headers.get('HX-Request'):
        return render(request, 'clients/partials/quick_request_success.html', {
            'request_type': request_type,
        })
    
    messages.success(request, 'Votre demande a été envoyée avec succès !')
    return redirect('clients:dashboard')


@login_required
def quote_detail(request, pk):
    """Display quote detail for client."""
    from apps.devis.models import Quote
    
    quote = get_object_or_404(Quote, pk=pk, client__email=request.user.email)
    
    return render(request, 'clients/quote_detail.html', {
        'quote': quote,
    })


@login_required
def quote_pdf_download(request, pk):
    """Download quote PDF."""
    from apps.devis.models import Quote
    from django.http import HttpResponse
    from core.services.document_generator import DocumentGenerator
    
    quote = get_object_or_404(Quote, pk=pk, client__email=request.user.email)
    
    # Toujours générer à la volée (filesystem éphémère sur Render)
    try:
        pdf_bytes = DocumentGenerator.generate_quote_pdf(quote, attach=False)
        response = HttpResponse(pdf_bytes, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="devis_{quote.number}.pdf"'
        return response
    except Exception as e:
        messages.error(request, f"Erreur lors de la génération du PDF: {str(e)}")
        return redirect('clients:quotes')


@login_required
@xframe_options_sameorigin
def quote_pdf_view(request, pk):
    """Afficher le PDF du devis en ligne (inline)."""
    from apps.devis.models import Quote
    from django.http import HttpResponse
    from core.services.document_generator import DocumentGenerator

    quote = get_object_or_404(Quote, pk=pk, client__email=request.user.email)

    # Toujours générer à la volée (filesystem éphémère sur Render)
    try:
        pdf_bytes = DocumentGenerator.generate_quote_pdf(quote, attach=False)
        resp = HttpResponse(pdf_bytes, content_type='application/pdf')
        resp['Content-Disposition'] = f'inline; filename="devis_{quote.number}.pdf"'
        return resp
    except Exception as e:
        # Retourner une page d'erreur simple au lieu d'un redirect (pour l'iframe)
        quote_detail_url = reverse_lazy('clients:quote_detail', kwargs={'pk': pk})
        return HttpResponse(
            f'<html><body style="display:flex;align-items:center;justify-content:center;'
            f'height:100vh;background:#12121a;color:#f6f7fb;font-family:Inter,sans-serif;'
            f'text-align:center;"><div><p style="font-size:1.1rem;margin-bottom:1rem;">'
            f'Aperçu indisponible</p><p style="color:rgba(246,247,251,0.5);font-size:0.9rem;">'
            f'Le PDF ne peut pas être affiché pour le moment.</p><a href="{quote_detail_url}" target="_top" '
            f'style="color:#0B2DFF;margin-top:1rem;display:inline-block;">Télécharger le PDF</a>'
            f'</div></body></html>',
            content_type='text/html',
            status=200,
        )


@login_required
def invoice_detail(request, pk):
    """Display invoice detail for client."""
    from apps.factures.models import Invoice
    
    invoice = get_object_or_404(
        Invoice,
        pk=pk,
        quote__client__email=request.user.email
    )
    
    return render(request, 'clients/invoice_detail.html', {
        'invoice': invoice,
    })


@login_required
def invoice_pdf_download(request, pk):
    """Download invoice PDF."""
    from apps.factures.models import Invoice
    
    invoice = get_object_or_404(
        Invoice,
        pk=pk,
        quote__client__email=request.user.email
    )
    
    if invoice.pdf:
        return FileResponse(
            invoice.pdf.open('rb'),
            as_attachment=True,
            filename=f"facture_{invoice.number}.pdf"
        )
    
    # Generate PDF if not exists
    from apps.factures.services.pdf_generator import InvoicePdfService
    
    try:
        pdf_bytes = InvoicePdfService.generate_invoice_pdf(invoice, attach=True)
        return FileResponse(
            iter([pdf_bytes]),
            as_attachment=True,
            filename=f"facture_{invoice.number}.pdf",
            content_type='application/pdf'
        )
    except Exception as e:
        messages.error(request, f"Erreur lors de la génération du PDF: {str(e)}")
        return redirect('clients:invoices')
