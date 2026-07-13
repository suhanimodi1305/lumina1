from django.contrib import admin
from .models import (
    EmployeeLoginLog, EmployeeAttendance, Lead, Opportunity,
    CallLog, SupportTicket, TicketReply, Campaign,
    InternalNote, CallbackRequest, SalesTarget
)


@admin.register(EmployeeLoginLog)
class EmployeeLoginLogAdmin(admin.ModelAdmin):
    list_display  = ('user', 'event', 'timestamp', 'ip_address')
    list_filter   = ('event',)
    search_fields = ('user__username', 'ip_address')
    readonly_fields = ('timestamp',)


@admin.register(EmployeeAttendance)
class EmployeeAttendanceAdmin(admin.ModelAdmin):
    list_display  = ('employee', 'date', 'status', 'check_in', 'check_out')
    list_filter   = ('status', 'date')
    search_fields = ('employee__username',)
    date_hierarchy = 'date'


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display  = ('lead_id', 'name', 'phone', 'source', 'stage', 'assigned_to', 'created_at')
    list_filter   = ('stage', 'source')
    search_fields = ('name', 'phone', 'email', 'lead_id')
    date_hierarchy = 'created_at'


@admin.register(Opportunity)
class OpportunityAdmin(admin.ModelAdmin):
    list_display  = ('opp_id', 'title', 'stage', 'value', 'probability', 'assigned_to')
    list_filter   = ('stage',)
    search_fields = ('title', 'opp_id')


@admin.register(CallLog)
class CallLogAdmin(admin.ModelAdmin):
    list_display  = ('call_id', 'employee', 'phone', 'direction', 'status', 'called_at')
    list_filter   = ('direction', 'status')
    search_fields = ('phone', 'customer_name', 'call_id')
    date_hierarchy = 'called_at'


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display  = ('ticket_id', 'customer_name', 'subject', 'priority', 'status', 'assigned_to', 'created_at')
    list_filter   = ('status', 'priority', 'channel')
    search_fields = ('ticket_id', 'customer_name', 'subject')
    date_hierarchy = 'created_at'


@admin.register(TicketReply)
class TicketReplyAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'author', 'is_internal', 'created_at')


@admin.register(Campaign)
class CampaignAdmin(admin.ModelAdmin):
    list_display  = ('camp_id', 'name', 'type', 'status', 'leads_generated', 'conversions', 'revenue')
    list_filter   = ('type', 'status')
    search_fields = ('name', 'camp_id')


@admin.register(InternalNote)
class InternalNoteAdmin(admin.ModelAdmin):
    list_display  = ('author', 'tag', 'content_preview', 'created_at')
    list_filter   = ('tag',)
    search_fields = ('content', 'author__username')

    def content_preview(self, obj):
        return obj.content[:60]
    content_preview.short_description = 'Content'


@admin.register(CallbackRequest)
class CallbackRequestAdmin(admin.ModelAdmin):
    list_display  = ('name', 'phone', 'status', 'assigned_to', 'is_resolved', 'created_at')
    list_filter   = ('status', 'is_resolved')
    search_fields = ('name', 'phone', 'email')
    date_hierarchy = 'created_at'


@admin.register(SalesTarget)
class SalesTargetAdmin(admin.ModelAdmin):
    list_display  = ('employee', 'date', 'target', 'achieved', 'pct')
    list_filter   = ('date',)
    search_fields = ('employee__username',)
    date_hierarchy = 'date'

    def pct(self, obj):
        return f'{obj.pct}%'
    pct.short_description = '% Achieved'
