"""
Admin registration for Orders app.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Order, OrderItem, OrderStatusLog, UserRequirement


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('name', 'brand', 'sku', 'shade', 'price', 'quantity', 'line_total_display')
    fields = ('name', 'brand', 'sku', 'shade', 'price', 'quantity', 'line_total_display')

    @admin.display(description='Line Total')
    def line_total_display(self, obj):
        return f'₹{obj.line_total}'


class OrderStatusLogInline(admin.TabularInline):
    model = OrderStatusLog
    extra = 1
    fields = ('status', 'message', 'location', 'timestamp')
    readonly_fields = ('timestamp',)


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'full_name', 'phone', 'city', 'status_badge',
                    'total_display', 'payment_method', 'created_at')
    list_filter  = ('status', 'payment_method', 'payment_status', 'state')
    search_fields = ('order_id', 'tracking_id', 'full_name', 'phone', 'email', 'pincode')
    readonly_fields = ('order_id', 'tracking_id', 'created_at', 'updated_at')
    list_per_page = 30
    date_hierarchy = 'created_at'
    inlines = [OrderItemInline, OrderStatusLogInline]

    fieldsets = (
        ('Order Identity', {
            'fields': ('order_id', 'tracking_id', 'user')
        }),
        ('Customer', {
            'fields': ('full_name', 'phone', 'email')
        }),
        ('Delivery Address', {
            'fields': ('address_line1', 'address_line2', 'city', 'state', 'pincode')
        }),
        ('Payment & Status', {
            'fields': ('payment_method', 'payment_status', 'status', 'estimated_delivery', 'delivered_at')
        }),
        ('Financials', {
            'fields': ('subtotal', 'delivery_charge', 'discount', 'total')
        }),
        ('Notes', {
            'fields': ('order_notes',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description='Status', ordering='status')
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

    @admin.display(description='Total', ordering='total')
    def total_display(self, obj):
        return f'₹{obj.total}'


class RequirementProductInline(admin.TabularInline):
    model = UserRequirement.products.through
    extra = 1
    verbose_name = 'Selected Product'
    verbose_name_plural = 'Selected Products'


@admin.register(UserRequirement)
class UserRequirementAdmin(admin.ModelAdmin):
    list_display = ('req_id', 'user', 'title', 'status_badge', 'priority_badge',
                    'city', 'assigned_to', 'created_at')
    list_filter  = ('status', 'priority', 'state')
    search_fields = ('req_id', 'user__username', 'user__email', 'title',
                     'full_name', 'phone', 'city')
    readonly_fields = ('req_id', 'created_at', 'updated_at')
    list_per_page = 30
    date_hierarchy = 'created_at'
    autocomplete_fields = ['user', 'assigned_to']
    filter_horizontal = ('products',)

    fieldsets = (
        ('Requirement Identity', {
            'fields': ('req_id', 'user', 'title', 'priority', 'status')
        }),
        ('Product Details', {
            'fields': ('products', 'custom_product', 'quantity', 'requirement_notes')
        }),
        ('Delivery Address', {
            'fields': ('full_name', 'phone', 'email',
                       'address_line1', 'address_line2', 'city', 'state', 'pincode')
        }),
        ('Employee Handling', {
            'fields': ('assigned_to', 'employee_notes', 'linked_order')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    @admin.display(description='Status', ordering='status')
    def status_badge(self, obj):
        colors = {
            'pending': '#f59e0b', 'accepted': '#3b82f6', 'processing': '#8b5cf6',
            'dispatched': '#ec4899', 'delivered': '#10b981',
            'rejected': '#ef4444', 'cancelled': '#6b7280',
        }
        color = colors.get(obj.status, '#64748b')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 10px;border-radius:20px;'
            'font-size:11px;font-weight:700;">{}</span>',
            color, obj.get_status_display()
        )

    @admin.display(description='Priority', ordering='priority')
    def priority_badge(self, obj):
        colors = {'low': '#94a3b8', 'normal': '#3b82f6', 'high': '#f97316', 'urgent': '#ef4444'}
        color = colors.get(obj.priority, '#64748b')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 8px;border-radius:20px;'
            'font-size:11px;font-weight:700;">{}</span>',
            color, obj.get_priority_display()
        )
