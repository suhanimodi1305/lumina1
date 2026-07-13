from django.contrib import admin
from .models import Coupon, CouponUsage


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display  = ('code', 'coupon_type', 'discount_value', 'scope', 'times_used',
                     'max_uses', 'valid_until', 'is_active', 'tier_required')
    list_filter   = ('coupon_type', 'scope', 'is_active', 'tier_required', 'is_referral')
    search_fields = ('code', 'description')
    readonly_fields = ('times_used', 'created_at')
    ordering      = ('-created_at',)


@admin.register(CouponUsage)
class CouponUsageAdmin(admin.ModelAdmin):
    list_display  = ('coupon', 'user', 'discount_applied', 'order_ref', 'used_at')
    list_filter   = ('used_at',)
    search_fields = ('coupon__code', 'user__username', 'order_ref')
    readonly_fields = ('used_at',)
