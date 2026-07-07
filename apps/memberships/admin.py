from django.contrib import admin
from .models import UserProfile, ReferralLog, TierAuditLog


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display  = ('user', 'tier', 'loyalty_points', 'staff_role', 'subscription_expires_at', 'tier_updated_at')
    list_filter   = ('tier', 'staff_role', 'admin_override_active')
    search_fields = ('user__username', 'user__email', 'referral_code')
    readonly_fields = ('referral_code', 'tier_updated_at')


@admin.register(ReferralLog)
class ReferralLogAdmin(admin.ModelAdmin):
    list_display  = ('referrer', 'referred_user', 'points_awarded', 'status', 'created_at')
    list_filter   = ('status',)


@admin.register(TierAuditLog)
class TierAuditLogAdmin(admin.ModelAdmin):
    list_display = ('profile', 'previous_tier', 'new_tier', 'points_deducted', 'reason', 'changed_by', 'created_at')
    readonly_fields = (
        'profile', 'changed_by', 'previous_tier', 'new_tier',
        'points_deducted', 'reason', 'created_at',
    )

    def has_add_permission(self, request):
        return False  # Immutable audit log — no manual additions

    def has_change_permission(self, request, obj=None):
        return False  # Immutable audit log — no edits
