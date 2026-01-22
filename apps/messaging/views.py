from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Count, Q
import json

from .models import Prospect, ProspectMessage, EmailTemplate, EmailCampaign, CampaignRecipient, ProspectActivity
from .services import send_prospect_email, send_prospection_template
from .forms import ProspectForm, CampaignForm

def staff_member_required(view_func):
    return user_passes_test(lambda u: u.is_staff)(view_func)

@staff_member_required
def inbox(request):
    """Main messaging interface - Outlook-style."""
    # Get messages
    messages_list = ProspectMessage.objects.select_related('prospect').order_by('-created_at')[:50]
    
    # Get prospects for autocomplete
    prospects = Prospect.objects.all().values('id', 'contact_name', 'email', 'company_name', 'status')
    prospects_json = json.dumps(list(prospects))
    
    # Stats
    total_sent = ProspectMessage.objects.filter(direction='outbound', status='sent').count()
    total_opened = ProspectMessage.objects.filter(direction='outbound', status='opened').count()
    open_rate = round((total_opened / total_sent * 100) if total_sent > 0 else 0)
    
    inbox_count = ProspectMessage.objects.filter(direction='inbound').count()
    drafts_count = ProspectMessage.objects.filter(status='draft').count()
    prospects_count = Prospect.objects.count()
    
    context = {
        'messages': messages_list,
        'prospects_json': prospects_json,
        'total_sent': total_sent,
        'open_rate': open_rate,
        'inbox_count': inbox_count,
        'drafts_count': drafts_count,
        'prospects_count': prospects_count,
    }
    
    return render(request, 'messaging/inbox.html', context)

@staff_member_required
def compose(request):
    """Compose email with Word-like editor."""
    # Get prospects for autocomplete in JS
    prospects_data = Prospect.objects.filter(email__isnull=False).values('id', 'contact_name', 'email', 'company_name')
    prospects_json = json.dumps(list(prospects_data))

    templates_qs = EmailTemplate.objects.filter(is_active=True)
    templates_list = list(templates_qs.values('id', 'name', 'subject', 'html_template'))
    templates_json = json.dumps(templates_list)
    
    context = {
        'prospects_json': prospects_json,
        'templates': templates_qs,
        'templates_json': templates_json,
    }
    
    return render(request, 'messaging/compose.html', context)

@staff_member_required
def prospect_list(request):
    """List all prospects."""
    status = request.GET.get('status')
    query = request.GET.get('q')
    
    prospects = Prospect.objects.all().order_by('-created_at')
    
    if status:
        prospects = prospects.filter(status=status)
        
    if query:
        prospects = prospects.filter(
            Q(contact_name__icontains=query) | 
            Q(email__icontains=query) |
            Q(company_name__icontains=query)
        )
    
    return render(request, 'messaging/prospect_list.html', {
        'prospects': prospects,
        'current_status': status
    })

@staff_member_required
def prospect_detail(request, pk):
    """View prospect details and history."""
    prospect = get_object_or_404(Prospect, pk=pk)
    activities = prospect.activities.all().order_by('-created_at')
    messages_history = prospect.messages.all().order_by('-created_at')
    
    return render(request, 'messaging/prospect_detail.html', {
        'prospect': prospect,
        'activities': activities,
        'messages_history': messages_history,
    })

@staff_member_required
def prospect_create(request):
    """Create a new prospect manually."""
    if request.method == 'POST':
        form = ProspectForm(request.POST)
        if form.is_valid():
            prospect = form.save()
            messages.success(request, f"Prospect {prospect.contact_name} ajouté.")
            return redirect('messaging:prospect_detail', pk=prospect.pk)
    else:
        form = ProspectForm()
    
    return render(request, 'messaging/prospect_form.html', {'form': form})

@staff_member_required
def prospect_edit(request, pk):
    """Edit a prospect."""
    prospect = get_object_or_404(Prospect, pk=pk)
    if request.method == 'POST':
        form = ProspectForm(request.POST, instance=prospect)
        if form.is_valid():
            entry = form.save()
            messages.success(request, "Prospect mis à jour.")
            return redirect('messaging:prospect_detail', pk=pk)
    else:
        form = ProspectForm(instance=prospect)
    
    return render(request, 'messaging/prospect_form.html', {'form': form, 'prospect': prospect})

@staff_member_required
def send_prospect_email_view(request, pk):
    """Send a prospection email to a prospect."""
    prospect = get_object_or_404(Prospect, pk=pk)
    
    if request.method == 'POST':
        template_slug = request.POST.get('template', 'prospection-standard')
        
        result = send_prospection_template(prospect, template_slug)
        
        if result.get('success'):
            messages.success(request, f"Email envoyé avec succès à {prospect.email}")
        else:
            messages.error(request, f"Erreur lors de l'envoi: {result.get('error')}")
        
        return redirect('messaging:prospect_detail', pk=prospect.pk)
    
    templates = EmailTemplate.objects.filter(is_active=True, category='prospection')
    
    return render(request, 'messaging/send_email.html', {
        'prospect': prospect,
        'templates': templates,
    })

@staff_member_required
@require_POST
def quick_send_email(request, pk):
    """Quick send email via HTMX."""
    prospect = get_object_or_404(Prospect, pk=pk)
    
    # Get raw body for JSON request
    if request.content_type == 'application/json':
        try:
            data = json.loads(request.body)
            subject = data.get('subject')
            content = data.get('html_content')
            
            from .services import send_email_brevo
            result = send_email_brevo(
                to_email=prospect.email,
                subject=subject,
                html_content=content,
                to_name=prospect.contact_name
            )
            
            if result.get('success'):
                # Log usage
                ProspectMessage.objects.create(
                    prospect=prospect,
                    subject=subject,
                    content=content,
                    direction='outbound',
                    status='sent',
                    message_id=result.get('message_id', '')
                )
                return JsonResponse({'success': True})
            else:
                return JsonResponse({'success': False, 'error': result.get('error')}, status=400)
                
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'error': 'Invalid JSON'}, status=400)
    
    # Fallback for old calls
    result = send_prospection_template(prospect)
    
    if result.get('success'):
        return HttpResponse(
            '<span class="text-green-400">✅ Email envoyé!</span>',
            content_type='text/html'
        )
    else:
        return HttpResponse(
            f'<span class="text-red-400">❌ {result.get("error")}</span>',
            content_type='text/html'
        )

@staff_member_required
def campaign_list(request):
    """List all email campaigns."""
    campaigns = EmailCampaign.objects.annotate(
        recipient_count=Count('recipients')
    ).all()
    
    return render(request, 'messaging/campaign_list.html', {
        'campaigns': campaigns,
    })

@staff_member_required
def campaign_detail(request, pk):
    """View campaign details and stats."""
    campaign = get_object_or_404(EmailCampaign, pk=pk)
    recipients = campaign.recipients.select_related('prospect').all()
    
    return render(request, 'messaging/campaign_detail.html', {
        'campaign': campaign,
        'recipients': recipients,
    })

@staff_member_required
def campaign_create(request):
    """Create a new email campaign."""
    if request.method == 'POST':
        form = CampaignForm(request.POST)
        if form.is_valid():
            campaign = form.save(commit=False)
            campaign.created_by = request.user
            campaign.save()
            
            # Add selected prospects
            prospect_ids = request.POST.getlist('prospects')
            if prospect_ids:
                prospects = Prospect.objects.filter(pk__in=prospect_ids)
                for prospect in prospects:
                    campaign.recipients.create(prospect=prospect)
            
            messages.success(request, f"Campagne '{campaign.name}' créée avec succès.")
            return redirect('messaging:campaign_detail', pk=campaign.pk)
    else:
        form = CampaignForm()
    
    prospects = Prospect.objects.filter(status__in=['new', 'contacted'])
    templates = EmailTemplate.objects.filter(is_active=True)
    
    return render(request, 'messaging/campaign_form.html', {
        'form': form,
        'prospects': prospects,
        'templates': templates,
    })

@staff_member_required
def template_list(request):
    """List all email templates."""
    templates = EmailTemplate.objects.all()
    
    return render(request, 'messaging/template_list.html', {
        'templates': templates,
    })

@staff_member_required
@require_POST
def import_prospects(request):
    """Import prospects from CSV or Quick Add."""
    # Check for Quick Add first
    if request.POST.get('quick_add') == '1':
        try:
            name = request.POST.get('contact_name')
            email = request.POST.get('email')
            company = request.POST.get('company_name', '')
            
            if not email:
                return JsonResponse({'success': False, 'error': 'Email required'})
                
            prospect, created = Prospect.objects.get_or_create(
                email=email,
                defaults={
                    'contact_name': name or email.split('@')[0],
                    'company_name': company,
                    'source': 'manual'
                }
            )
            return JsonResponse({
                'success': True, 
                'id': prospect.id,
                'name': prospect.contact_name
            })
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})

    # CSV Import
    import csv
    from io import StringIO
    
    csv_file = request.FILES.get('csv_file')
    if not csv_file:
        return JsonResponse({'error': 'No file provided'}, status=400)
    
    try:
        decoded_file = csv_file.read().decode('utf-8')
        reader = csv.DictReader(StringIO(decoded_file))
        
        created_count = 0
        errors = []
        
        for row in reader:
            try:
                Prospect.objects.get_or_create(
                    email=row.get('email', '').strip(),
                    defaults={
                        'contact_name': row.get('contact_name', row.get('name', '')).strip(),
                        'company_name': row.get('company_name', row.get('company', '')).strip(),
                        'phone': row.get('phone', '').strip(),
                        'sector': row.get('sector', 'other'),
                        'source': row.get('source', 'cold_email'),
                    }
                )
                created_count += 1
            except Exception as e:
                errors.append(f"{row.get('email')}: {str(e)}")
        
        return JsonResponse({
            'success': True,
            'created': created_count,
            'errors': errors
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@staff_member_required
@require_POST
def quick_add_prospect(request):
    """Quickly add a new prospect via AJAX."""
    try:
        data = json.loads(request.body)
        
        email = data.get('email', '').strip()
        name = data.get('name', '').strip()
        company = data.get('company', '').strip()
        
        if not email:
            return JsonResponse({'error': 'Email requis'}, status=400)
        
        # Check if prospect already exists
        existing = Prospect.objects.filter(email=email).first()
        if existing:
            return JsonResponse({
                'success': True,
                'prospect': {
                    'id': existing.id,
                    'email': existing.email,
                    'contact_name': existing.contact_name,
                    'company_name': existing.company_name,
                },
                'message': 'Prospect existant utilisé'
            })
        
        # Create new prospect
        prospect = Prospect.objects.create(
            email=email,
            contact_name=name or email.split('@')[0],
            company_name=company,
            source='cold_email',
            status='new'
        )
        
        return JsonResponse({
            'success': True,
            'prospect': {
                'id': prospect.id,
                'email': prospect.email,
                'contact_name': prospect.contact_name,
                'company_name': prospect.company_name,
            },
            'message': 'Prospect créé avec succès'
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@staff_member_required
@require_POST  
def send_email_api(request):
    """Send email via API - supports custom content from compose editor."""
    from .services import send_email_brevo
    
    try:
        data = json.loads(request.body)
        
        recipients = data.get('recipients', [])  # List of emails
        subject = data.get('subject', '')
        content = data.get('content', '')  # HTML content from TinyMCE
        
        if not recipients:
            return JsonResponse({'error': 'Aucun destinataire'}, status=400)
        
        if not subject:
            return JsonResponse({'error': 'Sujet requis'}, status=400)
        
        if not content:
            return JsonResponse({'error': 'Contenu requis'}, status=400)
        
        sent_count = 0
        errors = []
        
        for email in recipients:
            # Find or create prospect
            prospect, created = Prospect.objects.get_or_create(
                email=email,
                defaults={
                    'contact_name': email.split('@')[0],
                    'source': 'cold_email',
                    'status': 'new'
                }
            )
            
            # Send email via Brevo
            result = send_email_brevo(
                to_email=email,
                subject=subject,
                html_content=content
            )
            
            if result.get('success'):
                sent_count += 1
                
                # Log the message
                ProspectMessage.objects.create(
                    prospect=prospect,
                    subject=subject,
                    content=content,
                    direction='outbound',
                    status='sent',
                    message_id=result.get('message_id', '')
                )
                
                # Update prospect status
                if prospect.status == 'new':
                    prospect.status = 'contacted'
                    prospect.save()
                    
                # Log activity
                ProspectActivity.objects.create(
                    prospect=prospect,
                    activity_type='email_sent',
                    description=f"Email envoyé: {subject}"
                )
            else:
                errors.append(f"{email}: {result.get('error', 'Erreur inconnue')}")
        
        return JsonResponse({
            'success': True,
            'sent': sent_count,
            'total': len(recipients),
            'errors': errors
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
