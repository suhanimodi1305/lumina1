# Design Document — Premium Membership Tier System

## Overview

This design introduces a `apps/memberships` Django application that sits alongside the existing apps and provides tier management, referral/loyalty, VIP chat, and animated UI. All existing apps are extended minimally and non-destructively.

---

## Architecture

### New App: `apps/memberships`

```
apps/memberships/
  __init__.py
  apps.py
  models.py          # UserProfile, ReferralLog, TierAuditLog
  serializers.py     # TierSerializer
  decorators.py      # @tier_required('vip'), @tier_required('medium')
  context_processors.py  # user_tier_context (adds user_price_band, user_tier)
  signals.py         # post_save User → auto-create UserProfile
  middleware.py      # TierExpiryMiddleware
  views.py           # upgrade, redeem, doctor_consultation, memberships_admin
  urls.py
  admin.py
  migrations/
  templates/
    memberships/
      upgrade.html
      redeem.html
      doctor.html
      memberships_admin.html
```

### Modified Files (existing apps)

| File | Change |
|---|---|
| `apps/products/models.py` | Add `ayurvedic`, `pharmacy` to `RANGE_CHOICES` |
| `apps/products/views.py` | Handle `ayurvedic`/`pharmacy` ranges in `product_list` |
| `apps/chat/views.py` | Pass `price_ceiling` from user tier to `_resolve_products` and `get_ai_response` |
| `apps/chat/ai_service.py` | Accept `price_ceiling` param; inject tier context note into system prompt |
| `apps/accounts/views.py` | Call `_ensure_user_profile` after signup; handle referral code from signup form |
| `apps/accounts/forms.py` | Add optional `referral_code` field |
| `apps/orders/views.py` | Award loyalty points on order `delivered` status transition |
| `apps/employee/urls.py` | Add `memberships/` path |
| `apps/employee/views.py` | Add membership management view |
| `lumina/settings.py` | Add tier price constants; register `apps.memberships`; add context processor |
| `lumina/urls.py` | Add `path('doctor/', ...)` and `path('membership/', ...)` |
| `templates/base.html` | AOS CDN, tier badge, sidebar gating, Ayurvedic/Pharmacy nav items |
| `static/css/style.css` | `tier-glow`, hover-lift, tier card styles |

---

## Data Models

### `apps/memberships/models.py`

```python
import secrets, string
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

    user                  = models.OneToOneField(User, on_delete=models.CASCADE,
                                                  related_name='profile')
    tier                  = models.CharField(max_length=10, choices=TIER_CHOICES,
                                              default='normal')
    referral_code         = models.CharField(max_length=12, unique=True,
                                              default=_gen_referral_code)
    loyalty_points        = models.PositiveIntegerField(default=0)
    tier_updated_at       = models.DateTimeField(auto_now_add=True)
    subscription_expires_at = models.DateTimeField(null=True, blank=True)
    staff_role            = models.CharField(max_length=12, choices=STAFF_ROLE_CHOICES,
                                              default='none')
    # Admin override (used before payment gateway is configured)
    admin_override_tier   = models.CharField(max_length=10, choices=TIER_CHOICES,
                                              blank=True, default='')
    admin_override_active = models.BooleanField(default=False)

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
    referrer      = models.ForeignKey(UserProfile, on_delete=models.CASCADE,
                                       related_name='referrals_made')
    referred_user = models.ForeignKey(UserProfile, on_delete=models.CASCADE,
                                       related_name='referred_by')
    points_awarded = models.PositiveIntegerField(default=0)
    status         = models.CharField(max_length=12, choices=STATUS_CHOICES, default='pending')
    created_at     = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Referral Log'


class TierAuditLog(models.Model):
    """Immutable audit record for every tier change."""
    profile       = models.ForeignKey(UserProfile, on_delete=models.CASCADE,
                                       related_name='audit_logs')
    changed_by    = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    previous_tier = models.CharField(max_length=10)
    new_tier      = models.CharField(max_length=10)
    points_deducted = models.PositiveIntegerField(default=0)
    reason        = models.CharField(max_length=100, default='manual')
    created_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Tier Audit Log'
```

### `apps/chat/models.py` — Migration Addition

Add `is_vip_session` to the existing `Conversation` model via a new migration:

```python
is_vip_session = models.BooleanField(default=False)
```

Migration file: `apps/chat/migrations/0004_conversation_is_vip_session.py`

### `apps/products/models.py` — RANGE_CHOICES Addition

```python
RANGE_CHOICES = [
    ('korean',    'K-Beauty'),
    ('makeup',    'Makeup'),
    ('treatment', 'Treatment'),
    ('ayurvedic', 'Ayurvedic'),   # NEW
    ('pharmacy',  'Pharmacy'),    # NEW
]
```

Migration file: `apps/products/migrations/0002_product_range_ayurvedic_pharmacy.py`

---

## Settings Additions (`lumina/settings.py`)

```python
# ── MEMBERSHIP TIER PRICE BANDS ───────────────────────────────────────────────
NORMAL_PRICE_MAX  = 999     # ₹ — Normal tier ceiling
MEDIUM_PRICE_MAX  = 2499    # ₹ — Medium tier ceiling
# VIP: no ceiling (None)

# ── LOG & EARN POINTS CONFIG ──────────────────────────────────────────────────
REFERRAL_POINTS         = 100   # Points awarded to referrer on first login of referred user
PURCHASE_POINTS_RATE    = 1     # Points per ₹100 spent (floor division)
UPGRADE_POINTS_MEDIUM   = 500   # Points needed to upgrade Normal → Medium
UPGRADE_POINTS_VIP      = 1500  # Points needed to upgrade Medium → VIP

INSTALLED_APPS += ['apps.memberships']   # Add to INSTALLED_APPS

# Add to TEMPLATES context_processors:
# 'apps.memberships.context_processors.user_tier_context'

# Add to MIDDLEWARE (after AuthenticationMiddleware):
# 'apps.memberships.middleware.TierExpiryMiddleware'
```

---

## URL Routes

### `lumina/urls.py` additions

```python
path('membership/', include('apps.memberships.urls')),
path('doctor/',     include('apps.memberships.urls')),   # VIP doctor page lives here
```

### `apps/memberships/urls.py`

```python
from django.urls import path
from . import views

app_name = 'memberships'

urlpatterns = [
    path('upgrade/',           views.upgrade_page,         name='upgrade'),
    path('upgrade/confirm/',   views.upgrade_confirm,      name='upgrade_confirm'),
    path('redeem/',            views.redeem_points,        name='redeem'),
]

# VIP Doctor page (mounted at /doctor/ in root urls.py)
doctor_urlpatterns = [
    path('',   views.doctor_consultation, name='doctor'),
]
```

### `apps/employee/urls.py` addition

```python
path('memberships/', views.memberships_admin, name='memberships_admin'),
```

---

## Middleware: `apps/memberships/middleware.py`

Runs after `AuthenticationMiddleware`. Checks `subscription_expires_at` on every authenticated request and downgrades tier if expired.

```python
from django.utils import timezone

class TierExpiryMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            try:
                profile = request.user.profile
            except Exception:
                profile = _ensure_profile(request.user)
            
            if (profile.subscription_expires_at and
                    profile.subscription_expires_at < timezone.now() and
                    profile.tier != 'normal'):
                profile.tier = 'normal'
                profile.tier_updated_at = timezone.now()
                profile.save(update_fields=['tier', 'tier_updated_at'])
        
        return self.get_response(request)
```

---

## Context Processor: `apps/memberships/context_processors.py`

Injects `user_tier`, `user_price_band`, and `user_profile` into every template context.

```python
from django.conf import settings as django_settings

def user_tier_context(request):
    if not request.user.is_authenticated:
        return {'user_tier': 'normal', 'user_price_band': django_settings.NORMAL_PRICE_MAX}
    
    try:
        profile = request.user.profile
    except Exception:
        from apps.memberships.models import UserProfile
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
    
    tier = profile.effective_tier
    price_band = {
        'normal': django_settings.NORMAL_PRICE_MAX,
        'medium': django_settings.MEDIUM_PRICE_MAX,
        'vip':    None,   # no ceiling
    }.get(tier, django_settings.NORMAL_PRICE_MAX)

    return {
        'user_tier':        tier,
        'user_price_band':  price_band,
        'user_profile':     profile,
    }
```

---

## Signals: `apps/memberships/signals.py`

Auto-create `UserProfile` when a new `User` is saved.

```python
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
from .models import UserProfile

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)
```

`apps/memberships/apps.py` imports signals in `ready()`.

---

## Decorators: `apps/memberships/decorators.py`

```python
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
                messages.info(request,
                    f'This feature requires a {min_tier.upper()} membership.')
                return redirect('memberships:upgrade')
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
```

---

## Views: `apps/memberships/views.py`

### `upgrade_page` — GET `/membership/upgrade/`

- Login required; renders `memberships/upgrade.html`
- Context: tier card data (Normal/Medium/VIP), prices, benefits list
- AOS `data-aos="fade-up"` applied to each tier card in template (staggered 0/100/200ms delay)

### `upgrade_confirm` — POST `/membership/upgrade/confirm/`

- Login required; accepts `tier` POST param (`medium` or `vip`)
- If payment not configured: checks `admin_override_active` or returns payment-pending message
- On success: updates `UserProfile.tier`, sets `subscription_expires_at = now + 365 days`
- If already VIP: extends `subscription_expires_at` by 365 days
- Writes `TierAuditLog` entry; sends email via `apps.accounts.views._log_email`
- Sets session flag `tier_just_upgraded = True` for confetti trigger
- Redirects to `user_home` (confetti fires on `/me/` landing via session flag)

### `redeem_points` — GET+POST `/membership/redeem/`

- Login required; renders `memberships/redeem.html`
- Shows current points, upgrade cost, progress bar
- POST: validates sufficient points, deducts, upgrades tier, writes `TierAuditLog`
- VIP users see "You're already at the highest tier" message

### `doctor_consultation` — GET `/doctor/`

- Decorated with `@tier_required('vip')`
- Retrieves or creates a `Conversation` with `mode='doctor'` and `is_vip_session=True` for the user
  - Only one active VIP session per user (retrieved if exists, created if not)
- Fetches messages for that conversation only
- Renders `memberships/doctor.html` with gold accent theme
- AJAX send/receive reuses existing `chat:send_message` endpoint with the VIP conversation's `pk`

### `memberships_admin` — GET+POST `/employee/memberships/`

- Requires `request.user.is_authenticated` AND `profile.staff_role in ('admin', 'marketing')`
- Returns HTTP 403 for all other users
- GET: paginated table of all `UserProfile` records with tier, points, referral code, expiry
- POST (admin only): update a user's tier (writes `TierAuditLog`)
- Marketing users see read-only table (no edit form rendered)

---

## Chat Integration Changes

### `apps/chat/views.py`

`send_message` and `send_photo` gain access to `price_ceiling`:

```python
# Resolve price ceiling for this user
try:
    tier = request.user.profile.effective_tier
except Exception:
    tier = 'normal'

price_ceiling = {
    'normal': settings.NORMAL_PRICE_MAX,
    'medium': settings.MEDIUM_PRICE_MAX,
    'vip':    None,
}.get(tier, settings.NORMAL_PRICE_MAX)

ai_reply = get_ai_response(
    history,
    scan_context=scan_context,
    mode=conversation.mode,
    price_ceiling=price_ceiling,
    user_tier=tier,
)

# Filter resolved products by price ceiling
product_suggestions = _resolve_products(product_tags, price_ceiling=price_ceiling)
```

`_resolve_products` updated signature:

```python
def _resolve_products(product_tags, price_ceiling=None):
    qs = Product.objects.filter(sku__in=[t['sku'] for t in product_tags])
    if price_ceiling is not None:
        qs = qs.filter(price__lte=price_ceiling)
    # build and return suggestions list
```

### `apps/chat/ai_service.py`

`get_ai_response` and `_build_system_prompt` gain `user_tier` and `price_ceiling` params:

```python
TIER_CONTEXT_NOTES = {
    'normal': (
        "PRICE CONTEXT: Recommend only local, affordable brands available in India "
        f"at prices up to ₹{NORMAL_PRICE_MAX}. Prioritise budget-friendly options."
    ),
    'medium': (
        "PRICE CONTEXT: Recommend mid-range and exclusive brands available in India "
        f"at prices up to ₹{MEDIUM_PRICE_MAX}. Balance quality and price."
    ),
    'vip': (
        "PRICE CONTEXT: This user is a VIP member. Recommend the highest-end, "
        "premium global brands without price restriction."
    ),
}
```

The tier context note is appended to the system prompt inside `_build_system_prompt`.

---

## Log & Earn Integration

### Registration Flow (`apps/accounts/views.py` + `forms.py`)

1. `LuminaSignupForm` gains an optional `referral_code` `CharField` (not required, max_length=12).
2. In `signup` view after `login(request, user)`:
   - Call `UserProfile.objects.get_or_create(user=user)` (signal already creates it, this is a safety net)
   - If `referral_code` in POST: look up `UserProfile` by `referral_code`
     - If found: create `ReferralLog(referrer=found_profile, referred_user=new_profile, status='pending')`
     - If not found: silently skip, no error

3. `user_logged_in` signal handler (in `apps/memberships/signals.py`) on first login of a referred user:
   - Find any `ReferralLog` for this user with `status='pending'`
   - Award `REFERRAL_POINTS` to `referrer.loyalty_points`
   - Set `ReferralLog.status = 'confirmed'`

### Order Completion (`apps/orders/views.py`)

When order status transitions to `'delivered'` (in the employee order update view):

```python
# Award purchase loyalty points
if new_status == 'delivered' and order.user:
    try:
        profile = order.user.profile
        points = int(order.total // 100) * settings.PURCHASE_POINTS_RATE
        if points > 0:
            profile.loyalty_points += points
            profile.save(update_fields=['loyalty_points'])
    except Exception:
        pass  # never block order update
```

---

## Serializer: `apps/memberships/serializers.py`

```python
from datetime import datetime, timezone as dt_timezone

class TierSerializer:
    """Serialize/deserialize UserProfile tier state to/from a plain dict."""

    @staticmethod
    def serialize(profile) -> dict:
        expires = profile.subscription_expires_at
        return {
            'tier':                   profile.tier,
            'loyalty_points':         profile.loyalty_points,
            'referral_code':          profile.referral_code,
            'subscription_expires_at': expires.isoformat() if expires else None,
        }

    @staticmethod
    def deserialize(profile, data: dict):
        """Apply dict values back to profile (does not save)."""
        profile.tier            = data['tier']
        profile.loyalty_points  = data['loyalty_points']
        profile.referral_code   = data['referral_code']
        expires_raw = data.get('subscription_expires_at')
        profile.subscription_expires_at = (
            datetime.fromisoformat(expires_raw).replace(tzinfo=dt_timezone.utc)
            if expires_raw else None
        )
        return profile
```

---

## Templates

### `memberships/upgrade.html`

- Extends `base.html`
- 3 tier cards with `data-aos="fade-up"` and `data-aos-delay="0"`, `"100"`, `"200"`
- Each card: tier name, price, benefit bullets, "Upgrade Now" CTA button
- VIP card has gold border + `tier-glow` CSS class

### `memberships/redeem.html`

- Shows current points balance, progress bar to next tier, redeem button
- Progress bar: `width: (loyalty_points / threshold * 100)%`

### `memberships/doctor.html`

- Extends `base.html` with `{% block extra_css %}` for gold accent overrides
- `--sb-teal` overridden to `--sb-gold` (`#c9a96e`) for this page's active states
- Chat UI identical to `chat/room.html` but filtered to `is_vip_session=True` conversations
- Gold "VIP 1:1 Doctor" header badge

### `memberships/memberships_admin.html`

- Extends `base.html`
- Bootstrap table with user, tier badge, points, referral code, expiry
- Admin: inline tier `<select>` + Save button per row
- Marketing: same table, all inputs `disabled`

---

## Sidebar Changes (`templates/base.html`)

### AOS Integration

```html
<!-- in <head> -->
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/aos@2.3.4/dist/aos.css">

<!-- before </body> -->
<script src="https://cdn.jsdelivr.net/npm/aos@2.3.4/dist/aos.js"></script>
<script>AOS.init({ once: true, duration: 400 });</script>
```

### Tier Badge in Sidebar Footer

```html
<div class="sb-user-card">
  <div class="sb-user-avatar">{{ user.username|first|upper }}</div>
  <div>
    <div class="sb-user-name">{{ user.get_full_name|default:user.username }}</div>
    <div class="sb-user-role">
      {% if user_tier == 'vip' %}
        <span class="tier-badge tier-vip">VIP</span>
      {% elif user_tier == 'medium' %}
        <span class="tier-badge tier-medium">PLUS</span>
      {% else %}
        <span class="tier-badge tier-normal">FREE</span>
      {% endif %}
    </div>
  </div>
</div>
```

### PRO Badge Gating

Replace hardcoded `user.is_staff or user.username == 'suhani'` with:

```html
{% if user_tier == 'normal' %}
  <span class="sb-premium-badge">PRO</span>
{% endif %}
```

### VIP Doctor Sidebar Item (shown only to VIP)

```html
{% if user_tier == 'vip' %}
<a href="{% url 'memberships:doctor' %}" class="sb-item" style="color: var(--sb-gold);">
  <i class="bi bi-stars sb-icon" style="color: var(--sb-gold);"></i>
  <span class="sb-label">AI Doctor (VIP)</span>
</a>
{% endif %}
```

### Ayurvedic + Pharmacy Nav Items

```html
<a href="{% url 'products:list' %}?product_range=ayurvedic" class="sb-item">
  <i class="bi bi-flower2 sb-icon"></i>
  <span class="sb-label">Ayurvedic</span>
</a>
<a href="{% url 'products:list' %}?product_range=pharmacy" class="sb-item">
  <i class="bi bi-capsule sb-icon"></i>
  <span class="sb-label">Pharmacy</span>
</a>
```

---

## CSS Additions (`static/css/style.css`)

```css
/* ── TIER BADGES ── */
.tier-badge {
  display: inline-block;
  padding: .1rem .5rem;
  border-radius: 20px;
  font-size: .58rem;
  font-weight: 700;
  letter-spacing: .06em;
  text-transform: uppercase;
}
.tier-normal { background: rgba(255,255,255,.12); color: rgba(255,255,255,.5); }
.tier-medium { background: rgba(13,148,136,.25);  color: #0d9488; }
.tier-vip    { background: rgba(201,169,110,.25); color: #c9a96e; }

/* ── TIER GLOW (VIP elements) ── */
@keyframes tier-glow {
  0%, 100% { box-shadow: 0 0 0 0 rgba(201,169,110,0); border-color: #c9a96e; }
  50%       { box-shadow: 0 0 14px 4px rgba(201,169,110,.45); border-color: #e2c080; }
}
.vip-glow { animation: tier-glow 2s ease-in-out infinite; }

/* ── HOVER LIFT (tier cards + product cards) ── */
.tier-card, .product-card {
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.tier-card:hover, .product-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0,0,0,.12);
}

/* ── CONFETTI CANVAS ── */
#confetti-canvas {
  position: fixed;
  top: 0; left: 0;
  width: 100%; height: 100%;
  pointer-events: none;
  z-index: 99998;
}
```

---

## Confetti Animation

Vanilla JS confetti — no npm dependency. Triggered server-side via Django session flag `tier_just_upgraded`.

In `memberships/upgrade.html` (and `accounts/user_home.html`):

```html
{% if request.session.tier_just_upgraded %}
<canvas id="confetti-canvas"></canvas>
<script>
// Lightweight canvas confetti — ~60 lines vanilla JS
(function() {
  const canvas = document.getElementById('confetti-canvas');
  const ctx = canvas.getContext('2d');
  canvas.width = window.innerWidth;
  canvas.height = window.innerHeight;
  const pieces = Array.from({length: 120}, () => ({
    x: Math.random() * canvas.width,
    y: Math.random() * canvas.height - canvas.height,
    r: Math.random() * 6 + 4,
    d: Math.random() * 120,
    color: ['#c9a96e','#0d9488','#fff','#f59e0b','#e2c080'][Math.floor(Math.random()*5)],
    tilt: Math.random() * 10 - 10,
    tiltAngle: 0,
    tiltSpeed: Math.random() * 0.1 + 0.05,
  }));
  let frame, elapsed = 0;
  function draw() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    pieces.forEach(p => {
      p.tiltAngle += p.tiltSpeed;
      p.y += (Math.cos(p.d) + 1 + p.r / 2) * 0.8;
      p.x += Math.sin(p.d) * 0.6;
      p.tilt = Math.sin(p.tiltAngle) * 15;
      if (p.y > canvas.height) { p.y = -10; p.x = Math.random() * canvas.width; }
      ctx.beginPath();
      ctx.lineWidth = p.r / 2;
      ctx.strokeStyle = p.color;
      ctx.moveTo(p.x + p.tilt + p.r / 4, p.y);
      ctx.lineTo(p.x + p.tilt, p.y + p.tilt + p.r / 4);
      ctx.stroke();
    });
    elapsed += 16;
    if (elapsed < 3000) frame = requestAnimationFrame(draw);
    else { canvas.remove(); }
  }
  frame = requestAnimationFrame(draw);
  // Clear the session flag so confetti doesn't replay on refresh
  fetch('/membership/upgrade/confirm/', {method:'POST',
    headers:{'X-CSRFToken': document.cookie.match(/csrftoken=([^;]+)/)?.[1]||'',
             'Content-Type':'application/json'},
    body: JSON.stringify({clear_confetti: true})
  }).catch(()=>{});
})();
</script>
{% endif %}
```

The `upgrade_confirm` POST endpoint checks for `clear_confetti: true` in JSON body and calls `del request.session['tier_just_upgraded']`.

---

## Product List View — AOS Product Cards

In `templates/products/list.html`, each product card wrapper gains:

```html
<div class="product-card" data-aos="zoom-in">
  ...
</div>
```

---

## Migrations Required

| Migration | App | Description |
|---|---|---|
| `0001_initial.py` | `apps/memberships` | Creates `UserProfile`, `ReferralLog`, `TierAuditLog` |
| `0002_product_range_choices.py` | `apps/products` | Adds `ayurvedic`, `pharmacy` to `RANGE_CHOICES` (data migration not needed — Django CharField choices are not DB constraints) |
| `0004_conversation_is_vip_session.py` | `apps/chat` | Adds `is_vip_session` BooleanField to `Conversation` |

---

## Security Considerations

- `tier_required` decorator always falls back to `normal` on `RelatedObjectDoesNotExist` (never crashes)
- `TierExpiryMiddleware` uses `save(update_fields=...)` to avoid race conditions
- `TierAuditLog` is append-only; no update/delete operations
- Referral code lookup uses exact-match query on indexed unique field
- `memberships_admin` view checks `staff_role` not `is_staff` (different authorization plane)
- Admin override fields (`admin_override_tier`, `admin_override_active`) only settable via Django admin or direct DB — no user-facing form
- Confetti session flag cleared immediately after first render to prevent replay-on-refresh

---

## Components and Interfaces

This section documents the primary components of `apps/memberships` and the cross-cutting changes to existing apps, along with their public interfaces.

---

### `UserProfile` (model — `apps/memberships/models.py`)

Central model that extends `auth.User` with tier, referral, and loyalty data.

| Method / Property | Signature | Description |
|---|---|---|
| `effective_tier` | `@property → str` | Returns `admin_override_tier` when `admin_override_active` is `True`; otherwise returns `tier`. Never raises. |
| `__str__` | `→ str` | `"{username} [{effective_tier}]"` |

Key fields: `tier`, `referral_code` (unique, auto-generated), `loyalty_points`, `tier_updated_at`, `subscription_expires_at`, `staff_role`, `admin_override_tier`, `admin_override_active`.

---

### `ReferralLog` (model — `apps/memberships/models.py`)

Tracks referral relationships between `UserProfile` instances.

| Field | Type | Notes |
|---|---|---|
| `referrer` | FK → `UserProfile` | The referring user |
| `referred_user` | FK → `UserProfile` | The newly registered user |
| `points_awarded` | `PositiveIntegerField` | Points awarded to referrer |
| `status` | `CharField` | `pending` → `confirmed` or `revoked` |
| `created_at` | `DateTimeField` | Auto-set on creation |

---

### `TierAuditLog` (model — `apps/memberships/models.py`)

Append-only audit trail for every tier change. No update or delete operations are performed on this model.

| Field | Type | Notes |
|---|---|---|
| `profile` | FK → `UserProfile` | Subject of the change |
| `changed_by` | FK → `User` (nullable) | Actor; `None` for system-driven changes |
| `previous_tier` | `CharField` | Tier before the change |
| `new_tier` | `CharField` | Tier after the change |
| `points_deducted` | `PositiveIntegerField` | 0 for paid upgrades; cost for points redemptions |
| `reason` | `CharField` | One of `upgrade_purchase`, `points_redemption`, `admin_override`, `expiry_downgrade` |
| `created_at` | `DateTimeField` | Auto-set; ordering is `-created_at` |

---

### `TierExpiryMiddleware` (middleware — `apps/memberships/middleware.py`)

Runs on every authenticated request, positioned after `AuthenticationMiddleware` in `MIDDLEWARE`.

```
TierExpiryMiddleware.__call__(request) → HttpResponse
```

- Reads `request.user.profile.subscription_expires_at`
- If expired and `tier != 'normal'`: sets `tier = 'normal'`, saves with `update_fields=['tier', 'tier_updated_at']`
- Falls back to `UserProfile.objects.get_or_create` if `profile` relation is missing
- Never blocks the request; always calls `get_response(request)`

---

### `user_tier_context` (context processor — `apps/memberships/context_processors.py`)

Registered in `TEMPLATES[0]['OPTIONS']['context_processors']`. Injects tier variables into every template render.

```python
user_tier_context(request) -> dict
```

Return keys:

| Key | Type | Value |
|---|---|---|
| `user_tier` | `str` | `effective_tier` of the current user; `'normal'` for unauthenticated users |
| `user_price_band` | `int \| None` | `NORMAL_PRICE_MAX`, `MEDIUM_PRICE_MAX`, or `None` (VIP = no ceiling) |
| `user_profile` | `UserProfile \| None` | The profile instance; creates one on demand if missing |

---

### `tier_required` (decorator — `apps/memberships/decorators.py`)

```python
tier_required(min_tier: str) -> view decorator
```

- `min_tier` must be one of `'normal'`, `'medium'`, `'vip'`
- Unauthenticated users are redirected to `accounts:login`
- Users below `min_tier` receive a flash message and are redirected to `memberships:upgrade`
- Falls back to `'normal'` tier if `profile` relation is missing (never raises)
- `TIER_ORDER = {'normal': 0, 'medium': 1, 'vip': 2}`

---

### `TierSerializer` (serializer — `apps/memberships/serializers.py`)

Pure Python, no Django dependency at runtime.

```python
TierSerializer.serialize(profile: UserProfile) -> dict
```

Output keys: `tier`, `loyalty_points`, `referral_code`, `subscription_expires_at` (ISO 8601 string or `null`).

```python
TierSerializer.deserialize(profile: UserProfile, data: dict) -> UserProfile
```

Mutates and returns `profile` without calling `.save()`. Restores `subscription_expires_at` as a UTC-aware `datetime` or `None`.

---

### Views (`apps/memberships/views.py`)

| View function | Method | URL | Auth | Description |
|---|---|---|---|---|
| `upgrade_page` | GET | `/membership/upgrade/` | `@login_required` | Renders 3-tier card page with AOS delays |
| `upgrade_confirm` | GET/POST | `/membership/upgrade/confirm/` | `@login_required` | Processes paid tier upgrade; sets confetti session flag |
| `redeem_points` | GET/POST | `/membership/redeem/` | `@login_required` | Spends loyalty points to upgrade tier |
| `doctor_consultation` | GET | `/doctor/` | `@tier_required('vip')` | VIP-only 1:1 AI Doctor page |
| `memberships_admin` | GET/POST | `/employee/memberships/` | Staff role check | Admin/marketing membership management table |

**`upgrade_confirm` POST interface:**

- Form field `tier`: `'medium'` or `'vip'`
- JSON body `{"clear_confetti": true}`: clears the session flag and returns `{"ok": true}`

**`memberships_admin` POST interface:**

- Form fields `user_id` (UserProfile PK) and `tier` (`normal` / `medium` / `vip`)
- Returns HTTP 403 if caller lacks `admin` role

---

### Signals (`apps/memberships/signals.py`)

| Signal handler | Trigger | Action |
|---|---|---|
| `create_user_profile` | `post_save` on `User` (created=True) | `UserProfile.objects.get_or_create(user=instance)` |
| `confirm_referral_on_login` | `user_logged_in` | Finds pending `ReferralLog` for the logging-in user; awards `REFERRAL_POINTS` to referrer; sets status to `'confirmed'` |

---

### Chat Integration

**`apps/chat/views.py`** — `send_message` / `send_photo`:

```python
price_ceiling: int | None  # resolved from user's effective_tier via settings
```

Passed to `get_ai_response(…, price_ceiling=price_ceiling, user_tier=tier)` and to `_resolve_products(product_tags, price_ceiling=price_ceiling)`.

**`apps/chat/ai_service.py`** — `_build_system_prompt`:

```python
_build_system_prompt(mode: str, user_tier: str = 'normal', price_ceiling: int | None = None) -> str
```

Appends the appropriate `TIER_CONTEXT_NOTES[user_tier]` string to the system prompt.

**`_resolve_products` updated signature:**

```python
_resolve_products(product_tags: list[dict], price_ceiling: int | None = None) -> list[dict]
```

Filters `Product.objects.filter(sku__in=…)` by `price__lte=price_ceiling` when `price_ceiling` is not `None`.

---

## Correctness Properties

*A property is a characteristic or behavior that should hold true across all valid executions of a system — essentially, a formal statement about what the system should do. Properties serve as the bridge between human-readable specifications and machine-verifiable correctness guarantees.*

---

### Property 1: Auto-profile creation on user registration

*For any* new `User` created via `post_save`, a `UserProfile` must exist for that user with `tier == 'normal'` and a non-empty, unique `referral_code`.

**Validates: Requirements 1.2**

---

### Property 2: Tier expiry always downgrades to normal

*For any* `UserProfile` with `tier` in `{'medium', 'vip'}` and a `subscription_expires_at` strictly in the past, after `TierExpiryMiddleware` processes a request for that user, the profile's `tier` must equal `'normal'`.

**Validates: Requirements 1.4**

---

### Property 3: Price ceiling filters products correctly

*For any* collection of products with arbitrary prices and any `price_ceiling` value (integer or `None`), `_resolve_products` must return only products whose `price` is less than or equal to `price_ceiling`; when `price_ceiling` is `None` (VIP), all products must be returned.

**Validates: Requirements 2.2, 2.3, 2.4**

---

### Property 4: Context processor tier-to-price-band mapping is consistent

*For any* authenticated user with `effective_tier` in `{'normal', 'medium', 'vip'}`, `user_tier_context` must return a `user_price_band` that equals `NORMAL_PRICE_MAX`, `MEDIUM_PRICE_MAX`, or `None` respectively, matching the settings constants exactly.

**Validates: Requirements 2.5**

---

### Property 5: AI system prompt always contains the correct tier context note

*For any* tier value in `{'normal', 'medium', 'vip'}`, the AI system prompt constructed by `_build_system_prompt` must contain the corresponding `TIER_CONTEXT_NOTES` entry, and must not contain context notes for the other tiers.

**Validates: Requirements 3.3, 3.4, 3.5**

---

### Property 6: Referral points awarded exactly once per referred user login

*For any* pair of `UserProfile` instances where a `ReferralLog` with `status='pending'` exists, triggering `user_logged_in` for the referred user must increase `referrer.loyalty_points` by exactly `REFERRAL_POINTS` and set the log's `status` to `'confirmed'`. Triggering `user_logged_in` a second time must not award additional points.

**Validates: Requirements 6.2**

---

### Property 7: Purchase points formula is consistent with order total

*For any* order total `T >= 0`, the points awarded on delivery must equal `int(T // 100) * PURCHASE_POINTS_RATE`, and the profile's `loyalty_points` must increase by exactly that amount.

**Validates: Requirements 6.3**

---

### Property 8: Points redemption invariant

*For any* `UserProfile` with `loyalty_points >= cost` (where `cost` is `UPGRADE_POINTS_MEDIUM` or `UPGRADE_POINTS_VIP`), after a successful redemption via `redeem_points`: the profile's new `loyalty_points` must equal `old_loyalty_points - cost`, the profile's `tier` must equal the target tier, and a `TierAuditLog` entry must exist recording the deduction.

**Validates: Requirements 6.4, 6.5**

---

### Property 9: TierSerializer round-trip preserves all tier state

*For any* valid `UserProfile` state (any combination of `tier`, `loyalty_points`, `referral_code`, and `subscription_expires_at` including `None`), serializing then deserializing via `TierSerializer` must produce a profile whose `tier`, `loyalty_points`, `referral_code`, and `subscription_expires_at` are all equivalent to the originals.

**Validates: Requirements 11.2, 11.3**

---

### Property 10: Tier ordering is monotonic and total

*For any* two tier values `a` and `b` drawn from `{'normal', 'medium', 'vip'}`, `TIER_ORDER[a] < TIER_ORDER[b]` implies that `tier_required(b)` rejects a user at tier `a`, and `tier_required(a)` admits a user at tier `b`. The ordering must satisfy `normal < medium < vip` with no gaps or inversions.

**Validates: Requirements 1.3, 5.2**

---

## Error Handling

This section documents how the system handles each class of error condition.

---

### Missing `UserProfile`

**Where it can occur:** `TierExpiryMiddleware`, `user_tier_context`, `tier_required`, any view that calls `request.user.profile`.

**Strategy:** Every access site wraps the `profile` attribute lookup in a `try/except` block. On `RelatedObjectDoesNotExist` (or any exception), the code calls `UserProfile.objects.get_or_create(user=request.user)` to create a default `normal`-tier profile on demand. This is also the behaviour of the `create_user_profile` signal, which acts as the primary creation path.

**Impact:** No request ever fails with a 500 error due to a missing profile.

---

### Expired Subscription

**Where it is handled:** `TierExpiryMiddleware.__call__`

**Strategy:** On every authenticated request, if `subscription_expires_at < timezone.now()` and `tier != 'normal'`, the middleware sets `tier = 'normal'` and saves with `update_fields=['tier', 'tier_updated_at']`. This is a silent, automatic downgrade with no user-facing error. The user will observe their tier badge change to `FREE` on the next page load.

**Note:** The `effective_tier` property does not perform an expiry check; expiry is enforced exclusively by the middleware to avoid database writes inside property accessors.

---

### Invalid or Non-Existent Referral Code

**Where it is handled:** `apps/accounts/views.signup`

**Strategy:** After a successful `User` creation, if a `referral_code` was submitted in the form, the system attempts `UserProfile.objects.get(referral_code=submitted_code)`. If the lookup raises `UserProfile.DoesNotExist`, the referral is silently skipped and registration completes normally. No error message is displayed to the user (to prevent code enumeration). No `ReferralLog` is created.

---

### Insufficient Loyalty Points for Redemption

**Where it is handled:** `redeem_points` (POST path)

**Strategy:** Before deducting points, the view checks `profile.loyalty_points >= cost`. If the check fails, a `messages.error` flash message is added (`"You need {cost} points. You have {points}."`) and the view redirects back to `/membership/redeem/`. No points are deducted and no `TierAuditLog` entry is created.

---

### Downgrade Attempt via Upgrade Form

**Where it is handled:** `upgrade_confirm` (POST path)

**Strategy:** The view computes `TIER_ORDER[new_tier]` vs `TIER_ORDER[current_tier]`. If `new_tier` would be a downgrade (lower order), a `messages.info` flash is added and the user is redirected to the upgrade page. The only exception is a VIP user re-subscribing to VIP, which is allowed and extends `subscription_expires_at`.

---

### Unauthorized Access to Admin Views

**Where it is handled:** `memberships_admin`

**Strategy:** The view first checks `request.user.is_authenticated`; unauthenticated users are redirected to `accounts:login`. For authenticated users, `staff_role in ('admin', 'marketing')` or Django `is_staff`/`is_superuser` must be true; otherwise the view returns `HttpResponseForbidden('Access denied. Staff role required.')`. POST requests additionally require `staff_role == 'admin'` or Django staff; marketing users who POST receive `HttpResponseForbidden('Admin role required to modify tiers.')`.

---

### Invalid Tier Selection in Upgrade Form

**Where it is handled:** `upgrade_confirm` (POST path)

**Strategy:** `new_tier` is validated against `('medium', 'vip')`. Any other value results in `messages.error('Invalid tier selected.')` and a redirect to the upgrade page. No profile or audit log changes are made.

---

### Chat AI Tier Fallback

**Where it is handled:** `apps/chat/views.send_message`, `apps/chat/ai_service._build_system_prompt`

**Strategy:** If `request.user.profile.effective_tier` raises any exception, the view falls back to `tier = 'normal'` and `price_ceiling = NORMAL_PRICE_MAX`. The AI system prompt receives the Normal tier context note. A warning is logged via `logger.warning`. This ensures chat always works even if the membership system is misconfigured.

---

### Order Points Computation Failure

**Where it is handled:** `apps/orders/views` (order status transition to `delivered`)

**Strategy:** The entire points-award block is wrapped in `try/except Exception: pass`. An exception in the points computation (e.g. missing profile, database error) never blocks the order status update. Points are simply not awarded for that order.

---

### Confetti Session Flag Race / Replay

**Where it is handled:** Confetti JS + `upgrade_confirm`

**Strategy:** The confetti script fires a `fetch` POST to `/membership/upgrade/confirm/` with `{"clear_confetti": true}` immediately after starting the animation. The server deletes `request.session['tier_just_upgraded']`. On a page refresh the session key is gone and confetti does not replay.

---

## Testing Strategy

The testing strategy for the Premium Membership Tier System combines property-based tests for universal invariants with unit/example-based tests for specific flows and integration tests for cross-app behaviour.

---

### Property-Based Testing

**Library:** [`hypothesis`](https://hypothesis.readthedocs.io/) (Python property-based testing library)

**Minimum iterations:** 100 per property (Hypothesis default `max_examples=100`; increase to 200 for serialization tests)

**Tag format for test functions:** `# Feature: premium-membership-tiers, Property {N}: {property_text}`

Each Correctness Property from the design document is implemented as a single Hypothesis test. The table below maps properties to test strategies:

| Property | Test module | Hypothesis strategy |
|---|---|---|
| 1 — Auto-profile on registration | `tests/test_profile_creation.py` | `st.from_model(User)` |
| 2 — Expiry downgrades to normal | `tests/test_middleware.py` | `st.datetimes(max_value=now-1s)` for expiry, `st.sampled_from(['medium','vip'])` for tier |
| 3 — Price ceiling filters correctly | `tests/test_price_filter.py` | `st.lists(st.decimals(min_value=0, max_value=9999))` for prices, `st.integers(min_value=0)` for ceiling |
| 4 — Context processor mapping | `tests/test_context_processor.py` | `st.sampled_from(['normal','medium','vip'])` |
| 5 — AI prompt contains tier note | `tests/test_ai_service.py` | `st.sampled_from(['normal','medium','vip'])` |
| 6 — Referral points awarded once | `tests/test_signals.py` | `st.integers(min_value=0, max_value=10000)` for initial points |
| 7 — Purchase points formula | `tests/test_orders_points.py` | `st.decimals(min_value=0, max_value=100000)` for order total |
| 8 — Points redemption invariant | `tests/test_redeem.py` | `st.integers(min_value=500, max_value=100000)` for loyalty_points |
| 9 — Serializer round-trip | `tests/test_serializer.py` | Composite strategy: `(tier, loyalty_points, referral_code, expires_at\|None)` |
| 10 — Tier ordering monotonic | `tests/test_decorators.py` | `st.sampled_from(list(TIER_ORDER.items()))` for pairs |

---

### Unit / Example-Based Tests

These cover specific flows, edge cases, and integration points that are not universal properties:

| Test | Description |
|---|---|
| `test_upgrade_confirm_downgrade_rejected` | Verify that attempting to set a lower tier via `upgrade_confirm` redirects without writing changes |
| `test_upgrade_confirm_vip_extends_expiry` | Verify VIP re-subscribe extends `subscription_expires_at` by 365 days rather than resetting |
| `test_redeem_insufficient_points` | Verify flash message and no state change when points < cost |
| `test_redeem_already_vip` | Verify VIP users see "already at highest tier" message |
| `test_doctor_page_redirects_non_vip` | Verify `tier_required('vip')` redirects normal/medium users to upgrade page |
| `test_doctor_page_reuses_existing_conversation` | Verify `get_or_create` on `is_vip_session=True` returns the same `Conversation` on second request |
| `test_admin_view_marketing_readonly` | Verify marketing staff can GET but POST returns 403 |
| `test_admin_view_unauthorized_403` | Verify non-staff users receive 403 |
| `test_null_price_product_vip_only` | Verify product with `price=None` excluded for normal/medium, included for VIP |
| `test_invalid_referral_code_silent` | Verify registration succeeds with no `ReferralLog` when referral code doesn't match |
| `test_tier_audit_log_created_on_upgrade` | Verify `TierAuditLog` entry exists with correct `previous_tier`/`new_tier` after upgrade |
| `test_confetti_session_flag_cleared` | Verify POSTing `{"clear_confetti": true}` removes the session key |

---

### Integration Tests

Cross-app behaviour that requires multiple apps to be in a realistic state:

| Test | Apps involved | Description |
|---|---|---|
| `test_chat_price_ceiling_applied` | `chat`, `memberships` | Send a chat message as a normal-tier user; assert product suggestions exclude products above `NORMAL_PRICE_MAX` |
| `test_order_delivery_awards_points` | `orders`, `memberships` | Transition an order to `delivered`; assert `loyalty_points` increased by expected amount |
| `test_signup_with_referral_creates_log` | `accounts`, `memberships` | Register a new user with a valid referral code; assert `ReferralLog` with `status='pending'` exists |
| `test_referral_confirmed_on_login` | `accounts`, `memberships` | After registration with referral, log in the new user; assert referrer's `loyalty_points` increased |

---

### Testing Notes

- All property tests should use Django's `TestCase` or `SimpleTestCase` with `@settings(max_examples=100)` from Hypothesis.
- Property tests that touch the database should use `@given` with `django_db` marker (pytest-django) or inherit from `django.test.TestCase`.
- The `TierSerializer` round-trip test (Property 9) operates on plain Python objects and requires no database; use `SimpleTestCase`.
- The AI prompt test (Property 5) requires mocking the settings constants to prevent test environment coupling.
- Never test AWS, external APIs, or email delivery in unit/property tests — use `fail_silently=True` paths or mock `send_mail`.
- Audit log append-only invariant: no test should call `.update()` or `.delete()` on `TierAuditLog`; assert that only `INSERT` SQL is ever issued in tests covering audit log creation.
