# Implementation Plan: Premium Membership Tier System

## Overview

Implements the three-tier membership system (Normal / Medium / VIP), Log & Earn referral/loyalty programme, VIP 1:1 AI Doctor page, Ayurvedic/Pharmacy product ranges, tier-aware AI chat, animated UI components, and admin/marketing management views. Built as a new `apps/memberships` Django app with targeted modifications to existing apps.

## Tasks

- [ ] 1. Bootstrap `apps/memberships` app skeleton and settings constants
  - Create `apps/memberships/__init__.py` (empty)
  - Create `apps/memberships/apps.py` with `MembershipsConfig`; `name = 'apps.memberships'`; `ready()` imports `apps.memberships.signals`
  - Create `apps/memberships/migrations/__init__.py` (empty)
  - Register `apps.memberships` in `INSTALLED_APPS` in `lumina/settings.py`
  - Add tier price band constants to `lumina/settings.py`: `NORMAL_PRICE_MAX=999`, `MEDIUM_PRICE_MAX=2499`
  - Add Log & Earn point constants: `REFERRAL_POINTS=100`, `PURCHASE_POINTS_RATE=1`, `UPGRADE_POINTS_MEDIUM=500`, `UPGRADE_POINTS_VIP=1500`
  - _Requirements: 1.1, 2.1, 6.1_

- [ ] 2. Create `UserProfile`, `ReferralLog`, and `TierAuditLog` models and initial migration
  - Create `apps/memberships/models.py` with all three models as specified in design.md
  - `UserProfile`: OneToOne to User with `related_name='profile'`; fields: `tier` (choices normal/medium/vip, default normal), `referral_code` (unique, max_length=12, default=`_gen_referral_code`), `loyalty_points` (PositiveIntegerField default 0), `tier_updated_at` (auto_now_add), `subscription_expires_at` (nullable datetime), `staff_role` (none/marketing/admin, default none), `admin_override_tier`, `admin_override_active`
  - Implement `effective_tier` property: returns `admin_override_tier` when `admin_override_active` is True and `admin_override_tier` is non-empty, else returns `tier`
  - `ReferralLog`: FKs to UserProfile (referrer, referred_user), `points_awarded`, `status` (pending/confirmed/revoked), `created_at`
  - `TierAuditLog`: FK to UserProfile and nullable User (changed_by), `previous_tier`, `new_tier`, `points_deducted`, `reason`, `created_at`; Meta ordering `-created_at`
  - Generate migration `apps/memberships/migrations/0001_initial.py`
  - _Requirements: 1.1, 1.3, 6.1, 7.5, 8.1_

  - [ ] 2.1 Run initial migration
    - Run `python manage.py makemigrations memberships` then `python manage.py migrate`
    - Verify: `python manage.py shell -c "from apps.memberships.models import UserProfile; print('OK')"` prints OK

- [ ] 3. Add `is_vip_session` field to `Conversation` model and migrate
  - Add `is_vip_session = models.BooleanField(default=False)` to `Conversation` class in `apps/chat/models.py`
  - Generate and apply migration `apps/chat/migrations/0004_conversation_is_vip_session.py` (or next available number if it already exists)
  - _Requirements: 5.3, 5.6_

- [ ] 4. Add `ayurvedic` and `pharmacy` to Product `RANGE_CHOICES` and update product views
  - In `apps/products/models.py` add `('ayurvedic', 'Ayurvedic')` and `('pharmacy', 'Pharmacy')` to `RANGE_CHOICES` after `('treatment', 'Treatment')`
  - Generate and apply a Django migration (`apps/products/migrations/0002_product_range_choices.py`); note this is a choices-only change — no DB schema change is required, but migration documents the intent
  - Update `apps/products/views.py` `product_list` view to handle `product_range=ayurvedic` and `product_range=pharmacy` query-string filters, returning products grouped by brand and added to context
  - _Requirements: 4.1, 4.2, 4.3_

- [ ] 5. Create signals, middleware, context processor, and tier decorator
  - Create `apps/memberships/signals.py`:
    - `post_save` on `User` → `get_or_create` UserProfile (handles Requirement 1.2 and 1.5)
    - `user_logged_in` signal → find pending `ReferralLog` for the logging-in user; award `REFERRAL_POINTS` to referrer's `loyalty_points`; set `ReferralLog.status='confirmed'` (handles Requirement 6.2)
  - Create `apps/memberships/middleware.py` `TierExpiryMiddleware`: on each authenticated request check `subscription_expires_at`; if expired and tier != normal, downgrade to normal and save with `update_fields=['tier', 'tier_updated_at']` (handles Requirement 1.4)
  - Create `apps/memberships/context_processors.py` `user_tier_context`: return `user_tier` (effective_tier), `user_price_band` (normal→999, medium→2499, vip→None), `user_profile` for authenticated users; defaults to normal/999 for anonymous (handles Requirement 2.5)
  - Create `apps/memberships/decorators.py` `tier_required(min_tier)`: redirect unauthenticated to login; redirect insufficient tier to `memberships:upgrade` with informational message (handles Requirement 5.2)
  - Add `'apps.memberships.context_processors.user_tier_context'` to `TEMPLATES[0]['OPTIONS']['context_processors']` in `lumina/settings.py`
  - Add `'apps.memberships.middleware.TierExpiryMiddleware'` to `MIDDLEWARE` after `AuthenticationMiddleware` in `lumina/settings.py`
  - _Requirements: 1.2, 1.4, 1.5, 2.5, 5.2, 6.2_

- [ ] 6. Create `TierSerializer` in `apps/memberships/serializers.py`
  - Implement `TierSerializer.serialize(profile) -> dict`: returns dict with `tier`, `loyalty_points`, `referral_code`, `subscription_expires_at` (ISO string or null)
  - Implement `TierSerializer.deserialize(profile, data) -> profile`: applies dict values back; parses ISO datetime with UTC timezone; sets None for null expiry; does NOT call `save()`
  - _Requirements: 11.1, 11.2, 11.3_

- [ ] 7. Create memberships URL config and register all routes
  - Create `apps/memberships/urls.py` with `app_name='memberships'`; routes: `upgrade/` → `upgrade_page`, `upgrade/confirm/` → `upgrade_confirm`, `redeem/` → `redeem_points`; also define `doctor_urlpatterns` for the `/doctor/` mount
  - In `lumina/urls.py`: add `path('membership/', include('apps.memberships.urls', namespace='memberships'))` and `path('doctor/', include('apps.memberships.doctor_urlpatterns'))` importing from `apps.memberships.urls`
  - Add `path('memberships/', views.memberships_admin, name='memberships_admin')` to `apps/employee/urls.py`, importing `memberships_admin` from `apps.memberships.views`
  - _Requirements: 5.1, 6.4, 7.1, 8.2_

- [ ] 8. Create `upgrade_page` and `upgrade_confirm` views
  - `upgrade_page` (GET, `login_required`): build 3-tier context dicts (name, price, benefits list); render `memberships/upgrade.html`
  - `upgrade_confirm` (POST, `login_required`):
    - Check for `clear_confetti: true` JSON body; if present, delete session flag and return 204
    - Validate `tier` param is `medium` or `vip`
    - Update `UserProfile.tier` and `subscription_expires_at` (now + 365 days; extend if already VIP per Requirement 7.4)
    - Write `TierAuditLog` entry; send confirmation email via `apps.accounts.views._log_email`
    - Set `request.session['tier_just_upgraded'] = True`; redirect to `user_home`
  - _Requirements: 7.1, 7.2, 7.3, 7.4_

- [ ] 9. Create `redeem_points` view
  - `redeem_points` (GET + POST, `login_required`):
    - GET: render `memberships/redeem.html` with current points, next tier threshold (500 for Medium, 1500 for VIP), and progress bar percentage
    - POST: validate user has sufficient points; deduct `UPGRADE_POINTS_MEDIUM` or `UPGRADE_POINTS_VIP`; upgrade tier; update `tier_updated_at`; write `TierAuditLog`; set confetti session flag
    - VIP users see "You're already at the highest tier" message
  - _Requirements: 6.4, 6.5, 6.6_

- [ ] 10. Create `doctor_consultation` view
  - Decorate with `@tier_required('vip')`
  - `Conversation.objects.get_or_create(user=request.user, is_vip_session=True, defaults={'mode': 'doctor', 'title': 'VIP 1:1 Doctor Consultation'})`
  - Fetch messages for that conversation only (isolates VIP session per Requirement 5.4)
  - Build doctor mode prompts context
  - Render `memberships/doctor.html` with conversation, messages, mode prompts
  - _Requirements: 5.1, 5.2, 5.3, 5.4_

- [ ] 11. Create `memberships_admin` view
  - Access control: require `profile.staff_role in ('admin', 'marketing')` OR `request.user.is_staff`; else return `HttpResponseForbidden` (handles Requirement 8.5)
  - GET: all `UserProfile` records with `select_related('user')`; pass `is_admin` flag to template; render `memberships/memberships_admin.html`
  - POST (admin only): update target user's tier; update `tier_updated_at`; write `TierAuditLog`; redirect back
  - Marketing users see read-only table (no edit controls); non-staff gets 403 (Requirement 8.4)
  - _Requirements: 8.2, 8.3, 8.4, 8.5_

- [ ] 12. Update `apps/accounts/forms.py` and `apps/accounts/views.py` for referral code
  - Add optional `referral_code` `CharField` (max_length=12, required=False) to `LuminaSignupForm`
  - In `signup` view after `login(request, user)`:
    - Call `UserProfile.objects.get_or_create(user=user)` as safety net
    - If `referral_code` in POST: look up `UserProfile` by `referral_code`; if found and not self-referral, create `ReferralLog(referrer=found_profile, referred_user=new_profile, status='pending')`
    - Wrap entire block in try/except so signup never breaks regardless of outcome (Requirement 6.7)
  - _Requirements: 6.2, 6.7_

- [ ] 13. Award loyalty points on order delivery in `apps/orders/views.py`
  - Locate the order status update endpoint in the employee order management view
  - After saving `status='delivered'` transition: compute `points = int(order.total // 100) * settings.PURCHASE_POINTS_RATE`; award to `order.user.profile.loyalty_points` using `F()` expression and `update_fields`
  - Wrap in try/except so order update is never blocked
  - _Requirements: 6.3_

- [ ] 14. Checkpoint — Core backend complete
  - Run `python manage.py check` — no errors
  - Run `python manage.py migrate --check` — no unapplied migrations
  - Verify UserProfile auto-creates on new User creation via shell
  - Verify `tier_required('vip')` redirects Normal user to `/membership/upgrade/`

- [ ] 15. Update `apps/chat/ai_service.py` for tier-aware system prompts
  - Add `user_tier='normal'` and `price_ceiling=None` params to `get_ai_response()` and `_build_system_prompt()`
  - Define `TIER_CONTEXT_NOTES` dict with normal/medium/vip strings as specified in design.md (each referencing the appropriate price ceiling)
  - Append tier context note to system prompt inside `_build_system_prompt`
  - Existing callers without `user_tier` default to normal behaviour (Requirement 3.6)
  - _Requirements: 3.3, 3.4, 3.5, 3.6_

- [ ] 16. Update `apps/chat/views.py` for tier-aware product filtering
  - Resolve `effective_tier` and `price_ceiling` at the start of `send_message` and `send_photo` views (fallback to normal on any exception per Requirement 3.6)
  - Pass `user_tier` and `price_ceiling` to `get_ai_response`
  - Update `_resolve_products(product_tags, price_ceiling=None)`: filter `Product` queryset to `price__lte=price_ceiling` when ceiling is not None; exclude null-price products unless `price_ceiling` is None (VIP)
  - _Requirements: 2.2, 2.3, 2.4, 2.6, 3.1, 3.2_

- [ ] 17. Create membership templates (`upgrade.html`, `redeem.html`, `memberships_admin.html`)
  - `templates/memberships/upgrade.html`: 3 tier cards with `data-aos="fade-up"` and `data-aos-delay="0"`, `"100"`, `"200"` (staggered per Requirement 10.2); VIP card has `vip-glow` CSS class; confetti canvas + JS block triggered by `{% if request.session.tier_just_upgraded %}`
  - `templates/memberships/redeem.html`: loyalty points balance; progress bar toward next tier threshold; redeem form; VIP congratulations message
  - `templates/memberships/memberships_admin.html`: Bootstrap table with tier badges; admin sees tier `<select>` + Save per row; marketing sees all inputs `disabled`
  - _Requirements: 6.6, 7.1, 8.2, 8.3, 8.4, 10.2, 10.5_

- [ ] 18. Create VIP Doctor template (`templates/memberships/doctor.html`)
  - Extends `base.html`; `{% block extra_css %}` overrides `--sb-teal` to `var(--sb-gold)` (`#c9a96e`) for permanent gold accent (Requirement 5.5)
  - Gold "VIP 1:1 Doctor" badge header
  - Chat UI with message list, AJAX send form posting to existing `chat:send_message` endpoint using the VIP conversation's `pk`, quick prompts, photo upload button
  - Gold accent on send button and active states
  - _Requirements: 5.4, 5.5_

- [ ] 19. Update `templates/base.html` — AOS integration, tier badge, sidebar gating, and new nav items
  - Add AOS CDN `<link rel="stylesheet">` in `<head>` block and AOS `<script>` + `AOS.init({ once: true, duration: 400 })` before `</body>` (Requirement 10.1)
  - Replace hardcoded `user.is_staff or user.username == 'suhani'` PRO-badge checks with `{% if user_tier == 'normal' %}` (Requirement 9.1, 9.2, 9.3)
  - Add tier badge (FREE/PLUS/VIP) in sidebar footer user card using `user_tier` context variable with appropriate colour classes (Requirement 9.4)
  - Add VIP Doctor sidebar item (gold accent, only when `user_tier == 'vip'`, linking to `memberships:doctor`) (Requirement 9.5)
  - Add Ayurvedic and Pharmacy sidebar items in Shop section, styled consistently with existing items (Requirement 4.4)
  - Update `sb-user-role` label to show tier-aware role text
  - _Requirements: 4.4, 9.1, 9.2, 9.3, 9.4, 9.5, 10.1_

- [ ] 20. Update `templates/accounts/user_home.html` with loyalty points and confetti
  - Add Membership section: current tier badge, `loyalty_points` balance, progress bar toward next tier (500 for Medium, 1500 for VIP), links to upgrade and redeem pages (Requirement 6.6)
  - Add confetti canvas + vanilla JS block triggered by `{% if request.session.tier_just_upgraded %}` (clears session flag via fetch POST to `upgrade_confirm`) (Requirement 10.5)
  - _Requirements: 6.6, 10.5_

- [ ] 21. Add tier badge and animation CSS to `static/css/style.css`
  - Append `.tier-badge`, `.tier-normal`, `.tier-medium`, `.tier-vip` styles
  - Append `@keyframes tier-glow` (gold border pulse at 2-second interval) and `.vip-glow` class (Requirement 10.4)
  - Append `.tier-card, .product-card` hover-lift (`transform: translateY(-4px)`, `transition: transform 0.2s ease`) (Requirement 10.6)
  - Append `#confetti-canvas` fixed positioning styles
  - _Requirements: 10.4, 10.6_

- [ ] 22. Add `data-aos="zoom-in"` to product cards in `templates/products/list.html`
  - Find each product card wrapper element in the product grid
  - Add `data-aos="zoom-in"` attribute to each product card div
  - _Requirements: 10.3_

- [ ] 23. Register memberships models in Django admin (`apps/memberships/admin.py`)
  - Register `UserProfile` with `list_display`, `list_filter`, `search_fields`, `readonly_fields` (referral_code, tier_updated_at)
  - Register `ReferralLog` with `list_display`, `list_filter`
  - Register `TierAuditLog` with all fields readonly (append-only audit log)
  - _Requirements: 1.1, 6.1, 8.1_

- [ ] 24. Final checkpoint — full system check and smoke tests
  - Run `python manage.py check` — no errors
  - Run `python manage.py migrate --check` — no unapplied migrations
  - Verify UserProfile auto-creates on new User creation
  - Verify `TierSerializer` round-trip produces identical field values (Requirements 11.2, 11.3)
  - Verify `tier_required('vip')` redirects Normal user to `/membership/upgrade/` (Requirement 5.2)
  - Verify `ayurvedic` and `pharmacy` in `Product.RANGE_CHOICES` (Requirement 4.1)
  - Verify `Conversation` has `is_vip_session` field (Requirement 5.6)
  - Verify `get_ai_response` with `user_tier='vip'` includes "VIP member" in system prompt (Requirement 3.5)
  - Verify `memberships_admin` returns 403 for user without staff_role (Requirement 8.5)
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Payment gateway integration is intentionally deferred. The `upgrade_confirm` view directly upgrades the tier as a placeholder; the `admin_override_tier`/`admin_override_active` fields on `UserProfile` provide a manual override for production until payment is wired up (Requirement 7.5).
- The `tier_required` decorator and `TierExpiryMiddleware` both fall back to `normal` tier on any exception — the app never crashes due to a missing `UserProfile`.
- All referral and loyalty point operations are wrapped in try/except to never block the primary user flow (signup, order delivery).
- AOS is loaded from CDN (jsdelivr) at version 2.3.4 — no additional npm or pip dependencies required.
- Confetti is pure vanilla JS canvas (~60 lines) — no npm dependency.
- `TierAuditLog` is append-only; no update/delete operations are performed on it anywhere.
- The design document notes migration `0004_conversation_is_vip_session.py` for `apps/chat` — check the existing migrations directory and use the next available number if needed.
- Tasks marked with `*` are optional and can be skipped for a faster MVP.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["2.1"] },
    { "id": 1, "tasks": ["3", "4", "5", "6", "7"] },
    { "id": 2, "tasks": ["8", "9", "10", "11", "12", "13"] },
    { "id": 3, "tasks": ["14"] },
    { "id": 4, "tasks": ["15", "16", "17", "18", "19", "20", "21", "22", "23"] },
    { "id": 5, "tasks": ["24"] }
  ]
}
```
