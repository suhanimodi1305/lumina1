import secrets
import string

from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


def _gen_referral_code():
    """Generate a unique 10-character alphanumeric referral code."""
    alphabet = string.ascii_uppercase + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(10))


class UserProfile(models.Model):
    TIER_CHOICES = [
        ('normal', 'Normal'),
        ('medium', 'Medium'),
        ('vip',    'VIP'),
    ]
    STAFF_ROLE_CHOICES = [
        ('none',      'None'),
        ('marketing', 'Marketing'),
        ('admin',     'Admin'),
    ]

    user                    = models.OneToOneField(User, on_delete=models.CASCADE,
                                                   related_name='profile')
    tier                    = models.CharField(max_length=10, choices=TIER_CHOICES,
                                               default='normal')
    referral_code           = models.CharField(max_length=12, unique=True,
                                               default=_gen_referral_code)
    loyalty_points          = models.PositiveIntegerField(default=0)
    tier_updated_at         = models.DateTimeField(auto_now_add=True)
    subscription_expires_at = models.DateTimeField(null=True, blank=True)
    staff_role              = models.CharField(max_length=12, choices=STAFF_ROLE_CHOICES,
                                               default='none')
    # Admin override (used before payment gateway is configured)
    admin_override_tier     = models.CharField(max_length=10, choices=TIER_CHOICES,
                                               blank=True, default='')
    admin_override_active   = models.BooleanField(default=False)

    # ── Onboarding ────────────────────────────────────────────────────────────
    # Tracks how far through the first-time onboarding flow the user has gotten.
    # Steps: profile_setup → scan → quiz → done
    ONBOARDING_STEP_CHOICES = [
        ('profile_setup', 'Profile Setup'),
        ('scan',          'Selfie Scan'),
        ('quiz',          'Smart Quiz'),
        ('done',          'Completed'),
    ]
    onboarding_step = models.CharField(
        max_length=20,
        choices=ONBOARDING_STEP_CHOICES,
        default='profile_setup',
    )
    onboarding_complete = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'User Profile'

    def __str__(self):
        return f"{self.user.username} [{self.effective_tier}]"

    @property
    def effective_tier(self):
        """Returns the tier that should actually be enforced (admin override wins)."""
        if self.admin_override_active and self.admin_override_tier:
            return self.admin_override_tier
        return self.tier


class ReferralLog(models.Model):
    STATUS_CHOICES = [
        ('pending',   'Pending'),
        ('confirmed', 'Confirmed'),
        ('revoked',   'Revoked'),
    ]
    referrer       = models.ForeignKey(UserProfile, on_delete=models.CASCADE,
                                       related_name='referrals_made')
    referred_user  = models.ForeignKey(UserProfile, on_delete=models.CASCADE,
                                       related_name='referred_by')
    points_awarded = models.PositiveIntegerField(default=0)
    status         = models.CharField(max_length=12, choices=STATUS_CHOICES,
                                      default='pending')
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Referral Log'


class TierAuditLog(models.Model):
    """Immutable audit record for every tier change."""
    profile         = models.ForeignKey(UserProfile, on_delete=models.CASCADE,
                                        related_name='audit_logs')
    changed_by      = models.ForeignKey(User, on_delete=models.SET_NULL,
                                        null=True, blank=True)
    previous_tier   = models.CharField(max_length=10)
    new_tier        = models.CharField(max_length=10)
    points_deducted = models.PositiveIntegerField(default=0)
    reason          = models.CharField(max_length=100, default='manual')
    created_at      = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Tier Audit Log'
