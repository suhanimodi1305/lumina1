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
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_POST
from django.utils import timezone
from apps.scanner.models import ScanResult
from .forms import LuminaSignupForm, EditProfileForm, SavedAddressForm
from .models import SavedAddress, LoginHistory, UserDevice

logger = logging.getLogger(__name__)


# ── UA parser helper ──────────────────────────────────────────────────────────

def _parse_ua(user_agent_string):
    """Very lightweight UA parser — no external deps required."""
    ua = user_agent_string.lower()
    # Device type
    if any(x in ua for x in ('mobile', 'android', 'iphone', 'ipod')):
        device_type = 'mobile'
    elif any(x in ua for x in ('tablet', 'ipad')):
        device_type = 'tablet'
    else:
        device_type = 'desktop'
    # Browser
    if 'edg/' in ua or 'edge/' in ua:
        browser = 'Edge'
    elif 'opr/' in ua or 'opera' in ua:
        browser = 'Opera'
    elif 'chrome' in ua and 'safari' in ua:
        browser = 'Chrome'
    elif 'firefox' in ua:
        browser = 'Firefox'
    elif 'safari' in ua:
        browser = 'Safari'
    else:
        browser = 'Other'
    # OS
    if 'windows' in ua:
        os_name = 'Windows'
    elif 'mac os' in ua or 'macos' in ua:
        os_name = 'macOS'
    elif 'android' in ua:
        os_name = 'Android'
    elif 'iphone' in ua or 'ipad' in ua or 'ios' in ua:
        os_name = 'iOS'
    elif 'linux' in ua:
        os_name = 'Linux'
    else:
        os_name = 'Unknown'
    device_name = f'{browser} on {os_name}'
    return device_type, browser, os_name, device_name


def _record_login(user, request):
    """Record a LoginHistory entry and upsert UserDevice — call after successful login."""
    try:
        ua_string = request.META.get('HTTP_USER_AGENT', '')
        ip = (
            request.META.get('HTTP_X_FORWARDED_FOR', '').split(',')[0].strip()
            or request.META.get('REMOTE_ADDR')
        )
        device_type, browser, os_name, device_name = _parse_ua(ua_string)

        LoginHistory.objects.create(
            user=user,
            ip_address=ip or None,
            user_agent=ua_string[:500],
            device_type=device_type,
            browser=browser,
            os=os_name,
        )

        # Upsert device — match on user_agent fingerprint
        device, created = UserDevice.objects.get_or_create(
            user=user,
            browser=browser,
            os=os_name,
            device_type=device_type,
            defaults={
                'device_name': device_name,
                'ip_address': ip or None,
                'user_agent': ua_string[:500],
                'is_current': True,
            }
        )
        if not created:
            # Reset all is_current flags, then set this one
            UserDevice.objects.filter(user=user).update(is_current=False)
            device.ip_address = ip or None
            device.is_current = True
            device.save(update_fields=['ip_address', 'is_current', 'last_seen'])
        else:
            # Clear old current flags
            UserDevice.objects.filter(user=user).exclude(pk=device.pk).update(is_current=False)
    except Exception:
        pass  # never block login


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
            # New user → create profile first, then selfie scan
            _record_login(user, request)
            return redirect('profile_create')
        else:
            logger.warning("Failed signup attempt from IP: %s",
                           request.META.get('REMOTE_ADDR'))
    else:
        form = LuminaSignupForm()

    return render(request, 'accounts/signup.html', {'form': form})


@login_required
def user_home(request):
    """Home for logged-in regular users — routing hub with context."""
    if _is_staff(request.user):
        return redirect('employee:portal')

    from datetime import date
    from django.utils import timezone

    scans = ScanResult.objects.filter(
        user=request.user, is_demo=False
    ).prefetch_related('detected_concerns').order_by('-created_at')[:5]
    total_scans = ScanResult.objects.filter(user=request.user, is_demo=False).count()
    latest_scan = scans.first()

    # New user with no scan → send them through the first-time flow
    if total_scans == 0:
        return redirect('scanner:upload')

    has_scan = total_scans > 0
    days_since_last_scan = None
    reminder_due = False

    if latest_scan:
        days_since_last_scan = (timezone.now() - latest_scan.created_at).days
        reminder_due = days_since_last_scan >= 14

    # Today's routine log
    today_log = None
    try:
        from apps.progress.models import DailyRoutineLog
        today_log, _ = DailyRoutineLog.objects.get_or_create(
            user=request.user, log_date=date.today()
        )
    except Exception:
        pass

    return render(request, 'accounts/user_home.html', {
        'scans':                scans,
        'total_scans':          total_scans,
        'latest_scan':          latest_scan,
        'has_scan':             has_scan,
        'today_log':            today_log,
        'days_since_last_scan': days_since_last_scan,
        'reminder_due':         reminder_due,
    })


# ── Profile Create (post-signup step) ────────────────────────────────────────

@login_required
def profile_create(request):
    """
    Post-signup profile setup step.
    Collects first name, last name, age group, skin goals.
    On completion → redirect to /scan/ to start the first-time scan flow.
    """
    from apps.memberships.models import UserProfile

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name', '').strip()
        age_group  = request.POST.get('age_group', '').strip()
        skin_goal  = request.POST.get('skin_goal', '').strip()

        # Update Django User object
        if first_name:
            request.user.first_name = first_name
        if last_name:
            request.user.last_name = last_name
        request.user.save(update_fields=['first_name', 'last_name'])

        # Store profile details in session for pre-filling skin/diagnostic quizzes
        if age_group:
            request.session['profile_age_group'] = age_group
        if skin_goal:
            request.session['profile_skin_goal'] = skin_goal

        # Ensure UserProfile exists (doesn't require extra fields)
        try:
            from apps.memberships.models import UserProfile
            UserProfile.objects.get_or_create(user=request.user)
        except Exception:
            pass  # never block the flow

        # Mark profile as created so we don't redirect here again
        request.session['profile_created'] = True
        return redirect('scanner:upload')

    # GET — show the profile creation form
    return render(request, 'accounts/profile_create.html')


# ── Edit Profile ──────────────────────────────────────────────────────────────

@login_required
def edit_profile(request):
    """GET/POST /me/edit/ — edit personal info (name, email, phone, bio, age, goal)."""
    from apps.memberships.models import UserProfile

    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.method == 'POST':
        form = EditProfileForm(request.POST)
        if form.is_valid():
            d = form.cleaned_data
            request.user.first_name = d.get('first_name') or request.user.first_name
            request.user.last_name  = d.get('last_name')  or request.user.last_name
            if d.get('email'):
                request.user.email = d['email']
            request.user.save()

            # Store phone / bio / age_group / skin_goal on session (lightweight)
            if d.get('phone'):
                request.session['profile_phone'] = d['phone']
            if d.get('bio'):
                request.session['profile_bio'] = d['bio']
            if d.get('age_group'):
                request.session['profile_age_group'] = d['age_group']
            if d.get('skin_goal'):
                request.session['profile_skin_goal'] = d['skin_goal']

            messages.success(request, 'Profile updated successfully.')
            return redirect('accounts:edit_profile')
    else:
        form = EditProfileForm(initial={
            'first_name': request.user.first_name,
            'last_name':  request.user.last_name,
            'email':      request.user.email,
            'phone':      request.session.get('profile_phone', ''),
            'bio':        request.session.get('profile_bio', ''),
            'age_group':  request.session.get('profile_age_group', ''),
            'skin_goal':  request.session.get('profile_skin_goal', ''),
        })

    return render(request, 'accounts/edit_profile.html', {
        'form': form,
        'profile': profile,
    })


# ── Address Book ──────────────────────────────────────────────────────────────

@login_required
def address_list(request):
    """GET /me/addresses/ — list all saved addresses."""
    addresses = SavedAddress.objects.filter(user=request.user)
    form = SavedAddressForm()
    return render(request, 'accounts/address_list.html', {
        'addresses': addresses,
        'form': form,
    })


@login_required
def address_add(request):
    """POST /me/addresses/add/ — add a new address."""
    if request.method == 'POST':
        form = SavedAddressForm(request.POST)
        if form.is_valid():
            addr = form.save(commit=False)
            addr.user = request.user
            addr.save()
            messages.success(request, 'Address saved.')
        else:
            for field, errors in form.errors.items():
                for err in errors:
                    messages.error(request, f'{field}: {err}')
    return redirect('accounts:address_list')


@login_required
def address_edit(request, pk):
    """GET/POST /me/addresses/<pk>/edit/ — edit an existing address."""
    addr = get_object_or_404(SavedAddress, pk=pk, user=request.user)
    if request.method == 'POST':
        form = SavedAddressForm(request.POST, instance=addr)
        if form.is_valid():
            form.save()
            messages.success(request, 'Address updated.')
            return redirect('accounts:address_list')
    else:
        form = SavedAddressForm(instance=addr)
    return render(request, 'accounts/address_edit.html', {'form': form, 'address': addr})


@login_required
@require_POST
def address_delete(request, pk):
    """POST /me/addresses/<pk>/delete/ — delete an address."""
    addr = get_object_or_404(SavedAddress, pk=pk, user=request.user)
    addr.delete()
    messages.success(request, 'Address removed.')
    return redirect('accounts:address_list')


@login_required
@require_POST
def address_set_default(request, pk):
    """POST /me/addresses/<pk>/default/ — set as default."""
    addr = get_object_or_404(SavedAddress, pk=pk, user=request.user)
    addr.is_default = True
    addr.save()
    messages.success(request, f'{addr.get_label_display()} address set as default.')
    return redirect('accounts:address_list')


# ── Referral History ──────────────────────────────────────────────────────────

@login_required
def referral_history(request):
    """GET /me/referrals/ — show who you've referred and earnings."""
    from apps.memberships.models import UserProfile, ReferralLog
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    referrals = ReferralLog.objects.filter(
        referrer=profile
    ).select_related('referred_user__user').order_by('-created_at')

    total_earned = sum(r.points_awarded for r in referrals if r.status == 'confirmed')
    pending_count = referrals.filter(status='pending').count()

    return render(request, 'accounts/referral_history.html', {
        'referrals':     referrals,
        'profile':       profile,
        'total_earned':  total_earned,
        'pending_count': pending_count,
        'referral_code': profile.referral_code,
    })


# ── Login History ─────────────────────────────────────────────────────────────

@login_required
def login_history(request):
    """GET /me/login-history/ — show login events."""
    history = LoginHistory.objects.filter(user=request.user).order_by('-logged_in_at')[:50]
    return render(request, 'accounts/login_history.html', {'history': history})


# ── Devices ───────────────────────────────────────────────────────────────────

@login_required
def devices(request):
    """GET /me/devices/ — show recognized devices."""
    device_list = UserDevice.objects.filter(user=request.user).order_by('-last_seen')
    return render(request, 'accounts/devices.html', {'device_list': device_list})


@login_required
@require_POST
def device_remove(request, pk):
    """POST /me/devices/<pk>/remove/ — remove a device."""
    device = get_object_or_404(UserDevice, pk=pk, user=request.user)
    if device.is_current:
        messages.warning(request, "You can't remove the device you're currently using.")
    else:
        device.delete()
        messages.success(request, 'Device removed.')
    return redirect('accounts:devices')


@login_required
@require_POST
def device_trust(request, pk):
    """POST /me/devices/<pk>/trust/ — toggle trust for a device."""
    device = get_object_or_404(UserDevice, pk=pk, user=request.user)
    device.is_trusted = not device.is_trusted
    device.save(update_fields=['is_trusted'])
    return redirect('accounts:devices')


# ── Support Tickets (via Requirements) ───────────────────────────────────────

@login_required
def support_tickets(request):
    """GET /me/support/ — customer support tickets (repurposed from requirements)."""
    from apps.orders.models import UserRequirement
    tickets = UserRequirement.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'accounts/support_tickets.html', {'tickets': tickets})


# ── Export PDF ────────────────────────────────────────────────────────────────

@login_required
def export_pdf(request):
    """GET /me/export-pdf/ — export customer profile as PDF."""
    from apps.memberships.models import UserProfile, ReferralLog
    from apps.orders.models import Order
    from apps.coupons.models import CouponUsage

    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    scans = ScanResult.objects.filter(user=request.user, is_demo=False).order_by('-created_at')[:10]
    orders = Order.objects.filter(user=request.user).order_by('-created_at')[:10]
    coupon_uses = CouponUsage.objects.filter(user=request.user).order_by('-used_at')[:10]
    referrals = ReferralLog.objects.filter(
        referrer=profile, status='confirmed'
    ).select_related('referred_user__user')

    login_hist = LoginHistory.objects.filter(user=request.user).order_by('-logged_in_at')[:10]

    # Try weasyprint; if not available, render a print-ready HTML page
    try:
        from weasyprint import HTML, CSS
        html_string = render(request, 'accounts/export_pdf_content.html', {
            'profile': profile,
            'scans': scans,
            'orders': orders,
            'coupon_uses': coupon_uses,
            'referrals': referrals,
            'login_hist': login_hist,
            'now': timezone.now(),
        }).content.decode('utf-8')
        pdf = HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="lumina-profile-{request.user.username}.pdf"'
        return response
    except ImportError:
        # weasyprint not installed — show print-friendly HTML page instead
        return render(request, 'accounts/export_pdf_content.html', {
            'profile': profile,
            'scans': scans,
            'orders': orders,
            'coupon_uses': coupon_uses,
            'referrals': referrals,
            'login_hist': login_hist,
            'now': timezone.now(),
            'print_mode': True,
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
