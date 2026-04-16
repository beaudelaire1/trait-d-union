from django.contrib import admin

from .models import SimulatorReport


@admin.register(SimulatorReport)
class SimulatorReportAdmin(admin.ModelAdmin):
    list_display = (
        'email', 'tool_name', 'company', 'name',
        'pdf_sent_at', 'converted_to_lead', 'created_at',
    )
    list_filter = ('tool_slug', 'pdf_sent_at', 'created_at')
    search_fields = ('email', 'name', 'company', 'tool_name')
    readonly_fields = (
        'created_at', 'pdf_sent_at', 'ip_address', 'user_agent',
        'snapshot', 'send_error',
    )
    date_hierarchy = 'created_at'
