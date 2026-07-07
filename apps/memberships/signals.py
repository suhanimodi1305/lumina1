from django.db.models.signals import post_save
from django.contrib.auth.signals import user_logged_in
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.conf import settings


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        from .models import UserProfile
        UserProfile.objects.get_or_create(user=instance)


@receiver(user_logged_in)
def confirm_referral_on_login(sender, user, request, **kwargs):
    """On first login of a referred user, award points to referrer and confirm the referral."""
    try:
        from .models import ReferralLog
        pending = ReferralLog.objects.filter(
            referred_user__user=user,
            status='pending'
        ).select_related('referrer')
        for log in pending:
            log.referrer.loyalty_points += settings.REFERRAL_POINTS
            log.referrer.save(update_fields=['loyalty_points'])
            log.status = 'confirmed'
            log.save(update_fields=['status'])
    except Exception:
        pass  # never block login
