"""
Custom User admin — shows login history, order history, and email logs for every user.
"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe

from apps.employee.models import EmployeeLoginLog
from apps.orders.models import Order
from apps.accounts.models import EmailLog, SavedAddress, LoginHistory, UserDevice


# ── Inlines ───────────────────────────────────────────────────────────────────

class LoginLogInline(admin.TabularInline):
    """Shows the last 20 login/logout events for the user."""
    model = EmployeeLoginLog
    fk_name = 'user'
    extra = 0
    max_num = 20
    can_delete = False
    verbose_name = 'Login / Logout Event'
    verbose_name_plural = 'Login / Logout History (last 20)'
    readonly_fields = ('event_badge', 'timestamp', 'ip_address', 'user_agent_short', 'session_key')
    fields = ('event_badge', 'timestamp', 'ip_address', 'user_agent_short', 'session_key')
    ordering = ('-timestamp',)

    def has_add_permission(self, request, obj=None):
        return False

    @admin.display(description='Event')
    def event_badge(self, obj):
        color = '#10b981' if obj.event == 'login' else '#ef4444'
        label = obj.get_event_display()
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 10px;border-radius:20px;'
            'font-size:11px;font-weight:700;">{}</span>',
            color, label
        )

    @admin.display(description='User Agent')
    def user_agent_short(self, obj):
        ua = obj.user_agent or ''
        return ua[:80] + ('…' if len(ua) > 80 else '')


class UserOrderInline(admin.TabularInline):
    """Shows all orders placed by the user."""
    model = Order
    fk_name = 'user'
    extra = 0
    can_delete = False
    verbose_name = 'Order'
    verbose_name_plural = 'Order History'
    readonly_fields = ('order_link', 'status_badge', 'total_display', 'payment_method',
                       'payment_status', 'city', 'created_at')
    fields = ('order_link', 'status_badge', 'total_display', 'payment_method',
              'payment_status', 'city', 'created_at')
    ordering = ('-created_at',)

    def has_add_permission(self, request, obj=None):
        return False

    @admin.display(description='Order ID')
    def order_link(self, obj):
        url = reverse('admin:orders_order_change', args=[obj.pk])
        return format_html('<a href="{}">{}</a>', url, obj.order_id)

    @admin.display(description='Status')
    def status_badge(self, obj):
        colors = {
            'pending': '#f59e0b', 'confirmed': '#3b82f6', 'packed': '#8b5cf6',
            'shipped': '#ec4899', 'out_for_delivery': '#f97316',
            'delivered': '#10b981', 'cancelled': '#ef4444', 'returned': '#6b7280',
        }
        color = colors.get(obj.status, '#64748b')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 10px;border-radius:20px;'
            'font-size:11px;font-weight:700;">{}</span>',
            color, obj.get_status_display()
        )

    @admin.display(description='Total')
    def total_display(self, obj):
        return f'₹{obj.total}'


# ── Email Log Inline ──────────────────────────────────────────────────────────

class EmailLogInline(admin.TabularInline):
    """Shows all emails sent to the user."""
    model = EmailLog
    fk_name = 'user'
    extra = 0
    can_delete = False
    verbose_name = 'Email Sent'
    verbose_name_plural = 'Email History (outbound)'
    readonly_fields = ('type_badge', 'recipient', 'subject', 'body_preview',
                       'status_badge', 'ip_address', 'sent_at')
    fields = ('type_badge', 'recipient', 'subject', 'body_preview',
              'status_badge', 'ip_address', 'sent_at')
    ordering = ('-sent_at',)

    def has_add_permission(self, request, obj=None):
        return False

    @admin.display(description='Type')
    def type_badge(self, obj):
        colors = {
            'password_reset': '#0d9488',
            'welcome':        '#3b82f6',
            'notification':   '#8b5cf6',
            'other':          '#64748b',
        }
        color = colors.get(obj.email_type, '#64748b')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 10px;border-radius:20px;'
            'font-size:11px;font-weight:700;">{}</span>',
            color, obj.get_email_type_display()
        )

    @admin.display(description='Status')
    def status_badge(self, obj):
        color = '#10b981' if obj.status == 'sent' else '#ef4444'
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 10px;border-radius:20px;'
            'font-size:11px;font-weight:700;">{}</span>',
            color, obj.get_status_display()
        )


# ── Custom UserAdmin ──────────────────────────────────────────────────────────

class LuminaUserAdmin(BaseUserAdmin):
    """
    Extended User admin that adds:
    - Order history inline
    - Login / logout history inline
    - Extra columns in list view (email, staff flag, last login, order count)
    """
    inlines = [UserOrderInline, LoginLogInline, EmailLogInline]

    list_display = (
        'username', 'email', 'full_name', 'is_staff', 'is_active',
        'order_count', 'last_login', 'date_joined'
    )
    list_filter = BaseUserAdmin.list_filter + ('date_joined',)
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    list_per_page = 30

    @admin.display(description='Full Name')
    def full_name(self, obj):
        name = f'{obj.first_name} {obj.last_name}'.strip()
        return name or '—'

    @admin.display(description='Orders')
    def order_count(self, obj):
        count = obj.orders.count()
        if count == 0:
            return '—'
        url = (
            reverse('admin:orders_order_changelist')
            + f'?user__id__exact={obj.pk}'
        )
        return format_html('<a href="{}">{} order{}</a>', url, count, 's' if count != 1 else '')


# Re-register User with our extended admin
admin.site.unregister(User)
admin.site.register(User, LuminaUserAdmin)


# ── Standalone Email Log admin ────────────────────────────────────────────────

@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    """
    Full email log page — lists every outbound email with filters and search.
    """
    list_display  = ('type_badge', 'recipient', 'user_link', 'subject_short',
                     'status_badge', 'ip_address', 'sent_at')
    list_filter   = ('email_type', 'status', 'sent_at')
    search_fields = ('recipient', 'subject', 'user__username', 'user__email')
    readonly_fields = ('user', 'email_type', 'recipient', 'subject', 'body_preview',
                       'status', 'error_msg', 'sent_at', 'ip_address')
    ordering = ('-sent_at',)
    list_per_page = 50
    date_hierarchy = 'sent_at'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False   # Read-only log

    @admin.display(description='Type')
    def type_badge(self, obj):
        colors = {
            'password_reset': '#0d9488',
            'welcome':        '#3b82f6',
            'notification':   '#8b5cf6',
            'other':          '#64748b',
        }
        color = colors.get(obj.email_type, '#64748b')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 10px;border-radius:20px;'
            'font-size:11px;font-weight:700;">{}</span>',
            color, obj.get_email_type_display()
        )

    @admin.display(description='Status')
    def status_badge(self, obj):
        color = '#10b981' if obj.status == 'sent' else '#ef4444'
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 10px;border-radius:20px;'
            'font-size:11px;font-weight:700;">{}</span>',
            color, obj.get_status_display()
        )

    @admin.display(description='User')
    def user_link(self, obj):
        if not obj.user:
            return '—'
        url = reverse('admin:auth_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)

    @admin.display(description='Subject')
    def subject_short(self, obj):
        return obj.subject[:60] + ('…' if len(obj.subject) > 60 else '')


# ── Saved Address admin ───────────────────────────────────────────────────────

@admin.register(SavedAddress)
class SavedAddressAdmin(admin.ModelAdmin):
    list_display  = ('user', 'label', 'full_name', 'city', 'state', 'pincode', 'is_default')
    list_filter   = ('label', 'is_default', 'state')
    search_fields = ('user__username', 'full_name', 'city', 'pincode')
    ordering      = ('user__username',)


# ── Login History admin ───────────────────────────────────────────────────────

@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display  = ('user', 'ip_address', 'browser', 'os', 'device_type', 'logged_in_at')
    list_filter   = ('device_type', 'browser', 'os', 'logged_in_at')
    search_fields = ('user__username', 'ip_address', 'browser')
    ordering      = ('-logged_in_at',)
    readonly_fields = ('user', 'ip_address', 'user_agent', 'device_type',
                       'browser', 'os', 'logged_in_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# ── User Device admin ─────────────────────────────────────────────────────────

@admin.register(UserDevice)
class UserDeviceAdmin(admin.ModelAdmin):
    list_display  = ('user', 'device_name', 'device_type', 'browser', 'os',
                     'is_trusted', 'is_current', 'last_seen')
    list_filter   = ('device_type', 'browser', 'is_trusted', 'is_current')
    search_fields = ('user__username', 'device_name', 'ip_address')
    ordering      = ('-last_seen',)
