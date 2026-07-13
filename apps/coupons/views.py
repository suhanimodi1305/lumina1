"""
Coupons views — apply coupon (AJAX), user coupon wallet, admin management.
"""
import json
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from django.contrib.auth.decorators import user_passes_test

from .models import Coupon, CouponUsage


def _is_staff(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@user_passes_test(_is_staff, login_url='/accounts/login/')
def coupon_list(request):
    """Staff-facing coupon management list."""
    coupons = Coupon.objects.select_related('created_by').order_by('-created_at')
    return render(request, 'coupons/coupon_list.html', {
        'coupons': coupons,
        'total': coupons.count(),
        'active_count': coupons.filter(is_active=True).count(),
    })


@require_POST
def validate_coupon(request):
    """
    AJAX POST — validate a coupon code for the given cart total.
    Body: {'code': 'ABCD1234', 'cart_total': 1500}
    Returns: {'valid': True/False, 'message': '...', 'discount': 150.00}
    """
    try:
        data = json.loads(request.body)
    except Exception:
        data = request.POST.dict()

    code       = str(data.get('code', '')).upper().strip()
    cart_total = float(data.get('cart_total', 0) or 0)

    try:
        coupon = Coupon.objects.get(code=code)
    except Coupon.DoesNotExist:
        return JsonResponse({'valid': False, 'message': 'Invalid coupon code.'})

    user = request.user if request.user.is_authenticated else None
    is_valid, msg = coupon.is_valid(user=user, cart_total=cart_total)
    if not is_valid:
        return JsonResponse({'valid': False, 'message': msg})

    discount = float(coupon.compute_discount(cart_total))
    return JsonResponse({
        'valid':       True,
        'message':     f'Coupon applied! You save ₹{discount:.0f}',
        'discount':    discount,
        'coupon_type': coupon.coupon_type,
        'description': coupon.description,
    })


@login_required
def my_coupons(request):
    """User's available & used coupons."""
    used_codes = CouponUsage.objects.filter(user=request.user).values_list(
        'coupon__code', flat=True
    )
    from django.utils import timezone
    now = timezone.now()
    available = Coupon.objects.filter(
        is_active=True,
        valid_from__lte=now,
    ).filter(
        valid_until__gte=now
    ).exclude(
        code__in=used_codes
    ).order_by('-created_at')[:20]

    history = CouponUsage.objects.filter(user=request.user).select_related('coupon')[:20]

    return render(request, 'coupons/my_coupons.html', {
        'available': available,
        'history':   history,
    })
