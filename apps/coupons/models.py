"""
Coupons app — discount codes, loyalty redemption codes, referral bonuses.
"""
import string
import secrets
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


def _gen_code():
    """Generate a unique 8-character uppercase coupon code."""
    return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))


class Coupon(models.Model):
    """Reusable or single-use discount coupon."""

    TYPE_CHOICES = [
        ('percent',   'Percentage Off'),
        ('fixed',     'Fixed Amount Off'),
        ('free_ship', 'Free Shipping'),
    ]

    SCOPE_CHOICES = [
        ('all',       'All Products'),
        ('korean',    'Korean Range Only'),
        ('makeup',    'Makeup Only'),
        ('ayurvedic', 'Ayurvedic Only'),
        ('pharmacy',  'Pharmacy Only'),
    ]

    # Identity
    code            = models.CharField(max_length=30, unique=True, default=_gen_code)
    description     = models.CharField(max_length=200, blank=True)

    # Discount definition
    coupon_type     = models.CharField(max_length=12, choices=TYPE_CHOICES, default='percent')
    discount_value  = models.DecimalField(
        max_digits=8, decimal_places=2, default=10,
        help_text='Percentage (e.g. 15 = 15%) or fixed INR amount'
    )
    max_discount_inr = models.DecimalField(
        max_digits=8, decimal_places=2, null=True, blank=True,
        help_text='Cap for percentage coupons (leave blank for no cap)'
    )

    # Scope
    scope           = models.CharField(max_length=12, choices=SCOPE_CHOICES, default='all')
    min_order_value = models.DecimalField(
        max_digits=10, decimal_places=2, default=0,
        help_text='Minimum cart value to activate this coupon'
    )

    # Validity
    valid_from      = models.DateTimeField(default=timezone.now)
    valid_until     = models.DateTimeField(null=True, blank=True)

    # Usage limits
    max_uses        = models.PositiveIntegerField(
        null=True, blank=True,
        help_text='Total uses allowed (blank = unlimited)'
    )
    max_uses_per_user = models.PositiveSmallIntegerField(
        default=1,
        help_text='Times a single user can use this coupon'
    )
    times_used      = models.PositiveIntegerField(default=0)

    # Eligibility
    tier_required   = models.CharField(
        max_length=10, blank=True,
        help_text='Leave blank for all tiers. Set "medium" or "vip" to restrict.'
    )
    is_active       = models.BooleanField(default=True)
    is_referral     = models.BooleanField(
        default=False,
        help_text='Generated automatically from referral system'
    )

    created_by      = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='created_coupons'
    )
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Coupon'

    def __str__(self):
        return f'{self.code} — {self.coupon_type} {self.discount_value}'

    def is_valid(self, user=None, cart_total=0):
        """Check if coupon is currently valid for the given user and cart total."""
        now = timezone.now()
        if not self.is_active:
            return False, 'Coupon is inactive.'
        if now < self.valid_from:
            return False, 'Coupon is not yet active.'
        if self.valid_until and now > self.valid_until:
            return False, 'Coupon has expired.'
        if self.max_uses and self.times_used >= self.max_uses:
            return False, 'Coupon usage limit reached.'
        if cart_total < self.min_order_value:
            return False, f'Minimum order of ₹{self.min_order_value} required.'

        if user:
            user_uses = CouponUsage.objects.filter(coupon=self, user=user).count()
            if user_uses >= self.max_uses_per_user:
                return False, 'You have already used this coupon.'

            if self.tier_required:
                try:
                    tier = user.profile.effective_tier
                    tier_order = {'normal': 0, 'medium': 1, 'vip': 2}
                    if tier_order.get(tier, 0) < tier_order.get(self.tier_required, 0):
                        return False, f'This coupon requires {self.tier_required.upper()} membership.'
                except Exception:
                    pass

        return True, 'Valid'

    def compute_discount(self, cart_total):
        """Return the discount INR amount for the given cart total."""
        from decimal import Decimal
        total = Decimal(str(cart_total))
        if self.coupon_type == 'percent':
            disc = (total * self.discount_value / 100).quantize(Decimal('0.01'))
            if self.max_discount_inr:
                disc = min(disc, self.max_discount_inr)
        elif self.coupon_type == 'fixed':
            disc = min(self.discount_value, total)
        else:
            disc = Decimal('0')
        return disc


class CouponUsage(models.Model):
    """Records each time a coupon is used."""
    coupon  = models.ForeignKey(Coupon, on_delete=models.CASCADE, related_name='usages')
    user    = models.ForeignKey(User, on_delete=models.CASCADE, related_name='coupon_usages')
    order_ref = models.CharField(max_length=30, blank=True)
    discount_applied = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    used_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-used_at']

    def __str__(self):
        return f'{self.coupon.code} used by {self.user.username}'
