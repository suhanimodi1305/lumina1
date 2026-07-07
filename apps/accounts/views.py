"""
Authentication views for Lumina
Security hardening:
  - Removed hardcoded username bypass ('suhani')
  - Login attempt logging with IP
  - No information leakage on failed logins
"""
import time
import logging
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from apps.scanner.models import ScanResult
from .forms import LuminaSignupForm

logger = logging.getLogger(__name__)


def _is_staff(user):
    """
    Staff check using Django's built-in flags only.
    Never hardcode usernames — grant access via Django admin → is_staff checkbox.
    """
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def signup(request):
    if request.user.is_authenticated:
        return redirect('user_home')

    if request.method == 'POST':
        form = LuminaSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            # ── Handle referral code ──────────────────────────────────────────────────────
            try:
                from apps.memberships.models import UserProfile, ReferralLog
                referral_code = form.cleaned_data.get('referral_code', '').strip()
                if referral_code:
                    # Get or create the new user's profile
                    new_profile, _ = UserProfile.objects.get_or_create(user=user)
                    # Look up the referrer by code
                    referrer_profile = UserProfile.objects.filter(referral_code=referral_code).first()
                    if referrer_profile and referrer_profile.user != user:
                        # Create pending referral log
                        ReferralLog.objects.get_or_create(
                            referrer=referrer_profile,
                            referred_user=new_profile,
                            defaults={'status': 'pending', 'points_awarded': 100}
                        )
            except Exception:
                pass  # never block signup
            logger.info("New user registered: %s (IP: %s)",
                        user.username,
                        request.META.get('REMOTE_ADDR'))
            # Log welcome email
            _log_email(
                user=user,
                email_type='welcome',
                recipient=user.email,
                subject=f'Welcome to Lumina, {user.first_name or user.username}!',
                body_preview='Your Lumina account has been created successfully.',
                ip=request.META.get('REMOTE_ADDR'),
            )
            messages.success(request, f'Welcome to Lumina, {user.first_name or user.username}!')
            return redirect('user_home')
        else:
            logger.warning("Failed signup attempt from IP: %s",
                           request.META.get('REMOTE_ADDR'))
    else:
        form = LuminaSignupForm()

    return render(request, 'accounts/signup.html', {'form': form})


def user_home(request):
    """Home for logged-in regular users — limited access."""
    if not request.user.is_authenticated:
        return redirect('accounts:login')

    # Staff/admin go to employee portal — no hardcoded usernames
    if _is_staff(request.user):
        return redirect('employee:portal')

    scans = ScanResult.objects.filter(
        user=request.user, is_demo=False
    ).order_by('-created_at')[:3]
    total_scans = ScanResult.objects.filter(user=request.user, is_demo=False).count()
    latest_scan = scans.first()

    return render(request, 'accounts/user_home.html', {
        'scans':       scans,
        'total_scans': total_scans,
        'latest_scan': latest_scan,
    })


# ── Session status API ────────────────────────────────────────────────────────

def session_status(request):
    """
    Returns JSON with seconds remaining in the current session.
    Used by the client-side countdown timer.
    Called by the JS ping every 30 s.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'authenticated': False, 'seconds_left': 0})

    cookie_age = getattr(settings, 'SESSION_COOKIE_AGE', 7200)
    last_activity = request.session.get('_last_activity')
    if last_activity is None:
        seconds_left = cookie_age
    else:
        seconds_left = max(0, int(cookie_age - (time.time() - last_activity)))

    return JsonResponse({
        'authenticated': True,
        'seconds_left': seconds_left,
        'cookie_age': cookie_age,
    })


@require_POST
def session_ping(request):
    """
    Refreshes _last_activity so the sliding-window resets.
    Called when the user clicks "Stay Logged In" in the expiry modal.
    """
    if not request.user.is_authenticated:
        return JsonResponse({'ok': False, 'authenticated': False}, status=401)

    request.session['_last_activity'] = time.time()
    request.session.modified = True

    cookie_age = getattr(settings, 'SESSION_COOKIE_AGE', 7200)
    return JsonResponse({'ok': True, 'seconds_left': cookie_age})


# ── Email Logging Helper ──────────────────────────────────────────────────────

def _log_email(user, email_type, recipient, subject, body_preview='', ip=None, status='sent', error=''):
    """Silently saves an EmailLog entry. Never raises — logging must not break the main flow."""
    try:
        from .models import EmailLog
        EmailLog.objects.create(
            user=user,
            email_type=email_type,
            recipient=recipient,
            subject=subject,
            body_preview=body_preview[:500],
            status=status,
            error_msg=error,
            ip_address=ip,
        )
    except Exception:
        logger.exception("EmailLog write failed — this is non-fatal.")
