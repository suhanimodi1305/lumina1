from django.conf import settings as django_settings


def user_tier_context(request):
    if not request.user.is_authenticated:
        return {
            'user_tier': 'normal',
            'user_price_band': django_settings.NORMAL_PRICE_MAX,
            'SESSION_COOKIE_AGE': getattr(django_settings, 'SESSION_COOKIE_AGE', 7200),
        }

    try:
        profile = request.user.profile
    except Exception:
        from .models import UserProfile
        profile, _ = UserProfile.objects.get_or_create(user=request.user)

    tier = profile.effective_tier
    price_band = {
        'normal': django_settings.NORMAL_PRICE_MAX,
        'medium': django_settings.MEDIUM_PRICE_MAX,
        'vip':    None,
    }.get(tier, django_settings.NORMAL_PRICE_MAX)

    return {
        'user_tier':          tier,
        'user_price_band':    price_band,
        'user_profile':       profile,
        'SESSION_COOKIE_AGE': getattr(django_settings, 'SESSION_COOKIE_AGE', 7200),
    }
