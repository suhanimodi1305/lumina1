from django.contrib import admin
from .models import ProductReview, ReviewHelpful


@admin.register(ProductReview)
class ProductReviewAdmin(admin.ModelAdmin):
    list_display  = ('product', 'user', 'rating', 'status', 'scan_verified',
                     'purchase_verified', 'helpful_count', 'created_at')
    list_filter   = ('status', 'rating', 'skin_type', 'scan_verified', 'purchase_verified')
    search_fields = ('product__name', 'user__username', 'title')
    actions       = ['approve_reviews', 'reject_reviews']
    readonly_fields = ('created_at', 'updated_at')

    @admin.action(description='Approve selected reviews')
    def approve_reviews(self, request, queryset):
        updated = queryset.update(status='approved')
        self.message_user(request, f'{updated} review(s) approved.')

    @admin.action(description='Reject selected reviews')
    def reject_reviews(self, request, queryset):
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} review(s) rejected.')
