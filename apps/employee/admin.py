from django.contrib import admin
from django.utils.html import format_html
from .models import EmployeeLoginLog


@admin.register(EmployeeLoginLog)
class EmployeeLoginLogAdmin(admin.ModelAdmin):
    list_display  = ('user', 'email_display', 'event_badge', 'timestamp', 'ip_address', 'user_agent_short')
    list_filter   = ('event', 'timestamp')
    search_fields = ('user__username', 'user__email', 'ip_address')
    readonly_fields = ('user', 'event', 'timestamp', 'ip_address', 'user_agent', 'session_key')
    date_hierarchy = 'timestamp'
    list_per_page = 50
    ordering = ('-timestamp',)

    # Rename in admin sidebar
    class Meta:
        verbose_name = 'User Login Log'
        verbose_name_plural = 'User Login Logs'

    @admin.display(description='Email')
    def email_display(self, obj):
        return obj.user.email or '—'

    @admin.display(description='Event', ordering='event')
    def event_badge(self, obj):
        color = '#10b981' if obj.event == 'login' else '#ef4444'
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 10px;border-radius:20px;'
            'font-size:11px;font-weight:700;">{}</span>',
            color, obj.get_event_display()
        )

    @admin.display(description='User Agent')
    def user_agent_short(self, obj):
        ua = obj.user_agent or ''
        return ua[:60] + ('…' if len(ua) > 60 else '')
