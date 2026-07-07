from django.utils import timezone


class TierExpiryMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                profile = request.user.profile
            except Exception:
                from .models import UserProfile
                profile, _ = UserProfile.objects.get_or_create(user=request.user)

            if (profile.subscription_expires_at and
                    profile.subscription_expires_at < timezone.now() and
                    profile.tier != 'normal'):
                profile.tier = 'normal'
                profile.tier_updated_at = timezone.now()
                profile.save(update_fields=['tier', 'tier_updated_at'])

        return self.get_response(request)
