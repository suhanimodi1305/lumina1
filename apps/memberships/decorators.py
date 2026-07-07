from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def tier_required(min_tier):
    """Decorator that restricts a view to users at or above min_tier."""
    TIER_ORDER = {'normal': 0, 'medium': 1, 'vip': 2}

    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return redirect('accounts:login')
            try:
                tier = request.user.profile.effective_tier
            except Exception:
                tier = 'normal'
            if TIER_ORDER.get(tier, 0) < TIER_ORDER.get(min_tier, 0):
                messages.info(
                    request,
                    f'This feature requires a {min_tier.upper()} membership.'
                )
                return redirect('memberships:upgrade')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
