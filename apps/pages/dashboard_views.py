"""Dashboard views for the admin cockpit (Phase 5)."""
from decimal import Decimal
from datetime import date, timedelta
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum, Count, Avg, Q, F
from django.db.models.functions import TruncMonth, TruncWeek

from apps.devis.models import Quote
from apps.factures.models import Invoice
from apps.leads.models import Lead
from apps.clients.models import ClientProfile, Project


@staff_member_required
def dashboard_view(request):
    """Main dashboard view with KPIs and charts."""
    today = timezone.now().date()
    current_month_start = today.replace(day=1)
    last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
    year_start = today.replace(month=1, day=1)
    
    # ===================
    # KPIs principaux
    # ===================
    
    # Pipeline (devis envoyés non acceptés/rejetés)
    pipeline_quotes = Quote.objects.filter(
        status='sent'
    )
    pipeline_value = pipeline_quotes.aggregate(
        total=Sum('total_ttc')
    )['total'] or Decimal('0')
    
    # CA encaissé ce mois
    monthly_revenue = Invoice.objects.filter(
        status='paid',
        paid_at__gte=current_month_start
    ).aggregate(
        total=Sum('amount_paid')
    )['total'] or Decimal('0')
    
    # CA encaissé mois dernier (pour comparaison)
    last_month_revenue = Invoice.objects.filter(
        status='paid',
        paid_at__gte=last_month_start,
        paid_at__lt=current_month_start
    ).aggregate(
        total=Sum('amount_paid')
    )['total'] or Decimal('0')
    
    # Variation mensuelle
    if last_month_revenue > 0:
        revenue_variation = ((monthly_revenue - last_month_revenue) / last_month_revenue * 100)
    else:
        revenue_variation = 100 if monthly_revenue > 0 else 0
    
    # CA annuel
    yearly_revenue = Invoice.objects.filter(
        status='paid',
        paid_at__gte=year_start
    ).aggregate(
        total=Sum('amount_paid')
    )['total'] or Decimal('0')
    
    # ===================
    # Conversion Funnel
    # ===================
    
    # Leads ce mois
    monthly_leads = Lead.objects.filter(
        created_at__gte=current_month_start
    ).count()
    
    # Devis envoyés ce mois
    monthly_quotes_sent = Quote.objects.filter(
        created_at__gte=current_month_start,
        status__in=['sent', 'accepted', 'rejected']
    ).count()
    
    # Devis acceptés ce mois
    monthly_quotes_accepted = Quote.objects.filter(
        signed_at__gte=current_month_start,
        status='accepted'
    ).count()
    
    # Taux de conversion
    if monthly_quotes_sent > 0:
        conversion_rate = (monthly_quotes_accepted / monthly_quotes_sent * 100)
    else:
        conversion_rate = 0
    
    # ===================
    # Factures en retard
    # ===================
    overdue_invoices = Invoice.objects.filter(
        status='sent',
        due_date__lt=today
    )
    overdue_count = overdue_invoices.count()
    overdue_amount = overdue_invoices.aggregate(
        total=Sum('total_ttc')
    )['total'] or Decimal('0')
    
    # ===================
    # Projets actifs
    # ===================
    active_projects = Project.objects.exclude(
        status__in=['delivered', 'maintenance']
    ).count()
    
    # ===================
    # Graphiques - données pour Chart.js
    # ===================
    
    # Revenus mensuels (12 derniers mois)
    revenue_by_month = Invoice.objects.filter(
        status='paid',
        paid_at__gte=year_start
    ).annotate(
        month=TruncMonth('paid_at')
    ).values('month').annotate(
        total=Sum('amount_paid')
    ).order_by('month')
    
    months_labels = []
    revenue_data = []
    
    for item in revenue_by_month:
        if item['month']:
            months_labels.append(item['month'].strftime('%b %Y'))
            revenue_data.append(float(item['total'] or 0))
    
    # Pipeline par statut
    pipeline_by_status = Quote.objects.filter(
        created_at__gte=year_start
    ).values('status').annotate(
        count=Count('id'),
        value=Sum('total_ttc')
    )
    
    status_labels = []
    status_counts = []
    status_values = []
    status_colors = {
        'draft': '#9ca3af',
        'sent': '#3b82f6',
        'accepted': '#22c55e',
        'rejected': '#ef4444',
        'expired': '#f59e0b',
    }
    colors = []
    
    for item in pipeline_by_status:
        status_labels.append(dict(Quote.STATUS_CHOICES).get(item['status'], item['status']))
        status_counts.append(item['count'])
        status_values.append(float(item['value'] or 0))
        colors.append(status_colors.get(item['status'], '#6b7280'))
    
    # ===================
    # Récents
    # ===================
    recent_leads = Lead.objects.order_by('-created_at')[:5]
    recent_quotes = Quote.objects.order_by('-created_at')[:5]
    recent_invoices = Invoice.objects.order_by('-created_at')[:5]
    
    context = {
        # Date
        'today': today,
        
        # KPIs
        'pipeline_value': pipeline_value,
        'pipeline_count': pipeline_quotes.count(),
        'monthly_revenue': monthly_revenue,
        'last_month_revenue': last_month_revenue,
        'revenue_variation': revenue_variation,
        'yearly_revenue': yearly_revenue,
        
        # Conversion
        'monthly_leads': monthly_leads,
        'monthly_quotes_sent': monthly_quotes_sent,
        'monthly_quotes_accepted': monthly_quotes_accepted,
        'conversion_rate': conversion_rate,
        
        # Alertes
        'overdue_count': overdue_count,
        'overdue_amount': overdue_amount,
        'active_projects': active_projects,
        
        # Charts data (for Chart.js)
        'revenue_labels': months_labels,
        'revenue_data': revenue_data,
        'pipeline_labels': status_labels,
        'pipeline_data': status_counts,
        
        # Recent items
        'recent_leads': recent_leads,
        'recent_quotes': recent_quotes,
        'recent_invoices': recent_invoices,
    }
    
    return render(request, 'admin/dashboard.html', context)
