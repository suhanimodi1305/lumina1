import json
import logging
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from .models import ReferralLog, TierAuditLog, UserProfile
from .decorators import tier_required

logger = logging.getLogger(__name__)


def _get_or_create_profile(user):
    profile, _ = UserProfile.objects.get_or_create(user=user)
    return profile


def _log_email(user, subject, body):
    """Send a simple email via Django's mail — never raises."""
    try:
        from django.core.mail import send_mail
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [user.email], fail_silently=True)
    except Exception:
        pass


# ── Tier metadata used by upgrade page ────────────────────────────────────────
TIER_INFO = {
    'normal': {
        'name': 'Normal',
        'badge': 'FREE',
        'price': 'Free',
        'price_value': None,
        'color': 'rgba(255,255,255,.12)',
        'text_color': 'rgba(255,255,255,.5)',
        'benefits': [
            'AI skin consultations',
            'Product recommendations up to ₹999',
            'Basic skincare routines',
            'K-Beauty & Makeup AI access',
        ],
    },
    'medium': {
        'name': 'Medium',
        'badge': 'PLUS',
        'price': '₹999/year',
        'price_value': 999,
        'color': 'rgba(13,148,136,.25)',
        'text_color': '#0d9488',
        'benefits': [
            'All Normal benefits',
            'Product recommendations up to ₹2,499',
            'Priority AI responses',
            'Mid-range & exclusive brand access',
            'Earn 2× loyalty points',
        ],
    },
    'vip': {
        'name': 'VIP',
        'badge': 'VIP',
        'price': '₹2,499/year',
        'price_value': 2499,
        'color': 'rgba(201,169,110,.25)',
        'text_color': '#c9a96e',
        'benefits': [
            'All Medium benefits',
            'Unlimited product price access',
            'VIP 1:1 AI Doctor consultation',
            'Highest-end & premium global brands',
            'Earn 3× loyalty points',
            'Exclusive VIP badge',
        ],
    },
}


@login_required
def upgrade_page(request):
    """GET /membership/upgrade/ — show 3-tier cards."""
    profile = _get_or_create_profile(request.user)
    current_tier = profile.effective_tier

    tiers = [
        {**TIER_INFO['normal'], 'key': 'normal', 'is_current': current_tier == 'normal', 'aos_delay': '0'},
        {**TIER_INFO['medium'], 'key': 'medium', 'is_current': current_tier == 'medium', 'aos_delay': '100'},
        {**TIER_INFO['vip'],    'key': 'vip',    'is_current': current_tier == 'vip',    'aos_delay': '200'},
    ]

    context = {
        'tiers': tiers,
        'current_tier': current_tier,
        'profile': profile,
    }
    return render(request, 'memberships/upgrade.html', context)


@login_required
@require_http_methods(['GET', 'POST'])
def upgrade_confirm(request):
    """POST /membership/upgrade/confirm/ — process tier upgrade."""
    # Handle clear_confetti JSON ping from frontend
    if request.method == 'POST':
        try:
            body = json.loads(request.body)
            if body.get('clear_confetti'):
                request.session.pop('tier_just_upgraded', None)
                return JsonResponse({'ok': True})
        except (json.JSONDecodeError, Exception):
            pass

    if request.method == 'GET':
        return redirect('memberships:upgrade')

    profile = _get_or_create_profile(request.user)
    new_tier = request.POST.get('tier', '').strip()

    if new_tier not in ('medium', 'vip'):
        messages.error(request, 'Invalid tier selected.')
        return redirect('memberships:upgrade')

    # Tier order check — can't downgrade via this view
    # Exception: VIP can re-subscribe (extends expiry) but can't downgrade to medium/normal
    tier_order = {'normal': 0, 'medium': 1, 'vip': 2}
    current = profile.effective_tier
    if tier_order.get(new_tier, 0) < tier_order.get(current, 0):
        messages.info(request, f'You are already on the {current.upper()} tier.')
        return redirect('memberships:upgrade')
    if new_tier == current and current != 'vip':
        messages.info(request, f'You are already on the {current.upper()} tier.')
        return redirect('memberships:upgrade')

    previous_tier = profile.tier
    now = timezone.now()

    # Set subscription_expires_at: extend if VIP re-subscribing, else fresh 365 days
    if current == 'vip' and new_tier == 'vip' and profile.subscription_expires_at:
        profile.subscription_expires_at += timedelta(days=365)
    else:
        profile.subscription_expires_at = now + timedelta(days=365)

    profile.tier = new_tier
    profile.tier_updated_at = now
    profile.save(update_fields=['tier', 'tier_updated_at', 'subscription_expires_at'])

    # Write audit log
    TierAuditLog.objects.create(
        profile=profile,
        changed_by=request.user,
        previous_tier=previous_tier,
        new_tier=new_tier,
        points_deducted=0,
        reason='upgrade_purchase',
    )

    # Send confirmation email
    _log_email(
        request.user,
        f'Lumina Membership Upgrade — {new_tier.upper()}',
        f'Congratulations! Your membership has been upgraded to {new_tier.upper()}.\n'
        f'Your subscription is valid until {profile.subscription_expires_at.strftime("%d %B %Y")}.'
    )

    # Set confetti flag
    request.session['tier_just_upgraded'] = True

    messages.success(request, f'Welcome to {new_tier.upper()} membership!')
    return redirect('user_home')


@login_required
def redeem_points(request):
    """GET+POST /membership/redeem/ — spend loyalty points to upgrade tier."""
    profile = _get_or_create_profile(request.user)
    current_tier = profile.effective_tier
    points = profile.loyalty_points

    upgrade_costs = {
        'normal':  {'target': 'medium', 'cost': settings.UPGRADE_POINTS_MEDIUM, 'label': 'Upgrade to PLUS'},
        'medium':  {'target': 'vip',    'cost': settings.UPGRADE_POINTS_VIP,    'label': 'Upgrade to VIP'},
        'vip':     None,
    }
    upgrade_info = upgrade_costs.get(current_tier)

    if request.method == 'POST':
        if current_tier == 'vip':
            messages.info(request, "You're already at the highest tier!")
            return redirect('memberships:redeem')

        if not upgrade_info:
            messages.error(request, 'No upgrade path available.')
            return redirect('memberships:redeem')

        cost = upgrade_info['cost']
        if points < cost:
            messages.error(request, f'You need {cost} points. You have {points}.')
            return redirect('memberships:redeem')

        previous_tier = profile.tier
        new_tier = upgrade_info['target']
        now = timezone.now()

        profile.loyalty_points -= cost
        profile.tier = new_tier
        profile.tier_updated_at = now
        profile.subscription_expires_at = now + timedelta(days=365)
        profile.save(update_fields=['loyalty_points', 'tier', 'tier_updated_at', 'subscription_expires_at'])

        TierAuditLog.objects.create(
            profile=profile,
            changed_by=request.user,
            previous_tier=previous_tier,
            new_tier=new_tier,
            points_deducted=cost,
            reason='points_redemption',
        )

        request.session['tier_just_upgraded'] = True
        messages.success(request, f'Congratulations! Upgraded to {new_tier.upper()} using {cost} points.')
        return redirect('user_home')

    # GET — compute progress for template
    if upgrade_info:
        threshold = upgrade_info['cost']
        progress_pct = min(int((points / threshold) * 100), 100)
    else:
        threshold = None
        progress_pct = 100

    context = {
        'profile': profile,
        'points': points,
        'current_tier': current_tier,
        'upgrade_info': upgrade_info,
        'threshold': threshold,
        'progress_pct': progress_pct,
    }
    return render(request, 'memberships/redeem.html', context)


@login_required
@tier_required('vip')
def doctor_consultation(request):
    """GET /doctor/ — VIP-only 1:1 AI Doctor consultation page."""
    from apps.chat.models import Conversation, Message

    conversation, _ = Conversation.objects.get_or_create(
        user=request.user,
        is_vip_session=True,
        defaults={
            'mode':  'doctor',
            'title': 'VIP 1:1 Doctor Consultation',
        },
    )

    chat_messages = conversation.messages.all()

    mode_prompts = [
        "I have persistent acne on my face",
        "I have dark spots and pigmentation",
        "My skin is very dry and sensitive",
        "I need a prescription-grade skincare routine",
        "I want to discuss my Lumina scan results",
        "I have a skin concern I'd like to discuss privately",
    ]

    context = {
        'conversation': conversation,
        'messages':     chat_messages,
        'mode_prompts': mode_prompts,
    }
    return render(request, 'memberships/doctor.html', context)


def memberships_admin(request):
    """GET+POST /employee/memberships/ — membership management for admin/marketing staff."""
    from django.http import HttpResponseForbidden
    if not request.user.is_authenticated:
        return redirect('accounts:login')

    # Access control
    try:
        profile = request.user.profile
        staff_role = profile.staff_role
    except Exception:
        staff_role = 'none'

    has_access = (
        request.user.is_staff or
        request.user.is_superuser or
        staff_role in ('admin', 'marketing')
    )
    if not has_access:
        return HttpResponseForbidden('Access denied. Staff role required.')

    is_admin = (
        request.user.is_staff or
        request.user.is_superuser or
        staff_role == 'admin'
    )

    if request.method == 'POST':
        if not is_admin:
            return HttpResponseForbidden('Admin role required to modify tiers.')

        target_user_id = request.POST.get('user_id')
        new_tier = request.POST.get('tier', '').strip()

        if target_user_id and new_tier in ('normal', 'medium', 'vip'):
            try:
                target_profile = UserProfile.objects.select_related('user').get(pk=target_user_id)
                previous_tier = target_profile.tier
                if previous_tier != new_tier:
                    target_profile.tier = new_tier
                    target_profile.tier_updated_at = timezone.now()
                    target_profile.save(update_fields=['tier', 'tier_updated_at'])
                    TierAuditLog.objects.create(
                        profile=target_profile,
                        changed_by=request.user,
                        previous_tier=previous_tier,
                        new_tier=new_tier,
                        points_deducted=0,
                        reason='admin_override',
                    )
                    messages.success(request, f'Updated {target_profile.user.username} to {new_tier.upper()}.')
            except UserProfile.DoesNotExist:
                messages.error(request, 'User not found.')

        return redirect('employee:memberships_admin')

    # GET — list all profiles
    all_profiles = UserProfile.objects.select_related('user').order_by('user__username')

    context = {
        'all_profiles': all_profiles,
        'is_admin': is_admin,
    }
    return render(request, 'memberships/memberships_admin.html', context)
