# Requirements Document

## Introduction

The Premium Membership Tier System introduces a structured access model for Lumina AI, a skincare and beauty app built on Django. The system defines three membership tiers — Normal (free), Medium (mid-tier paid), and VIP (premium paid) — each granting progressively richer product recommendations, lower effective price-point access, and exclusive features.

This feature encompasses:
- A `UserProfile` model extending Django's built-in `auth.User` with tier, referral, and loyalty point data
- Tier-aware product filtering and price-band presentation
- A dedicated VIP-only 1:1 AI Doctor consultation page (the existing `doctor` chat mode works in group chat; this creates a separate, exclusive entry point)
- A Log & Earn referral/loyalty programme (modelled after the Trya Hair Care referral system)
- Admin and Marketing staff roles with dedicated management views
- New product range categories: Ayurvedic and Pharmacy
- Animated UI components using AOS (Animate On Scroll) and CSS keyframe animations to replace the current static appearance

---

## Glossary

- **Membership_System**: The Django application (new app `apps/memberships`) managing tiers, subscriptions, referrals, and loyalty points.
- **Normal_Tier**: The free default membership level available to all registered users.
- **Medium_Tier**: The mid-tier paid membership level with reduced price-band access and exclusive pricing.
- **VIP_Tier**: The highest paid membership level with the lowest price-band access and exclusive 1:1 AI Doctor consultation.
- **UserProfile**: A Django model extending `auth.User` with fields for membership tier, referral code, and loyalty points.
- **Tier_Gate**: A Django decorator or mixin that restricts a view to users of a specified tier or above.
- **Price_Band**: A named price range used to filter product recommendations. Three bands exist: `normal_band`, `medium_band`, `vip_band`.
- **AI_Doctor_Page**: A dedicated URL and view (`/doctor/`) providing VIP users a private, single-user 1:1 AI consultation conversation.
- **Referral_Code**: A unique alphanumeric code tied to a UserProfile, shareable to earn referral credits.
- **Loyalty_Points**: Numerical credits earned by Normal and Medium tier users through purchases and referrals; redeemable for tier upgrades.
- **Log_And_Earn**: The referral/loyalty subsystem that tracks code usage, awards points, and supports tier upgrade redemption.
- **Marketing_Role**: A staff role that can create and manage tier-based promotions and product highlights but cannot modify memberships.
- **Admin_Role**: A superuser or `is_staff` role with full membership management capabilities.
- **Product_Range**: The classification field on the `Product` model; valid values include `korean`, `makeup`, `treatment`, `ayurvedic`, `pharmacy`.
- **AOS_Library**: Animate On Scroll — the JavaScript/CSS animation library to be integrated into Lumina's base template.
- **Tier_Badge**: A visual indicator in the sidebar and profile showing the user's current membership tier.

---

## Requirements

### Requirement 1: User Profile and Tier Model

**User Story:** As a registered user, I want my account to carry a membership tier, so that the application can personalise product recommendations and feature access based on my subscription level.

#### Acceptance Criteria

1. THE Membership_System SHALL create a `UserProfile` model with a one-to-one relationship to `auth.User`, containing fields: `tier` (choices: `normal`, `medium`, `vip`; default `normal`), `referral_code` (unique, auto-generated), `loyalty_points` (integer, default 0), `tier_updated_at` (datetime), and `subscription_expires_at` (nullable datetime).
2. WHEN a new user registers via `apps/accounts`, THE Membership_System SHALL automatically create a `UserProfile` with `tier = normal` and a unique `referral_code`.
3. THE Membership_System SHALL expose a `user.profile.tier` property accessible from templates and views without additional queries.
4. WHEN `subscription_expires_at` is set and the current datetime exceeds `subscription_expires_at`, THE Membership_System SHALL downgrade the user's `tier` to `normal` on the next authenticated request.
5. IF the `UserProfile` record does not exist for an authenticated user, THE Membership_System SHALL create a default `UserProfile` for that user on demand rather than raising a `RelatedObjectDoesNotExist` exception.

---

### Requirement 2: Tier-Based Product Price Bands

**User Story:** As a user, I want product recommendations filtered to my membership tier's price bracket, so that I only see products appropriate for my subscription level.

#### Acceptance Criteria

1. THE Membership_System SHALL define three price bands in configurable settings: `NORMAL_PRICE_MAX` (default ₹999), `MEDIUM_PRICE_MAX` (default ₹2,499), `VIP_PRICE_MAX` (no upper limit).
2. WHEN a Normal_Tier user requests product recommendations, THE Membership_System SHALL return all products with `price <= NORMAL_PRICE_MAX`, and IF no products satisfy this criterion, THE Membership_System SHALL return an empty list with a "No recommendations available" message rather than an error.
3. WHEN a Medium_Tier user requests product recommendations, THE Membership_System SHALL return products with `price <= MEDIUM_PRICE_MAX`, and IF no products satisfy this criterion, THE Membership_System SHALL return an empty list rather than an error.
4. WHEN a VIP_Tier user requests product recommendations, THE Membership_System SHALL return all products regardless of price.
5. THE Membership_System SHALL expose a template context variable `user_price_band` containing the maximum price value for the current user's tier, available on every authenticated page via the context processor.
6. IF a product has no price set (`price` is null), THE Membership_System SHALL include that product only for VIP_Tier users.

---

### Requirement 3: Tier-Aware AI Product Recommendations in Chat

**User Story:** As a user chatting with the Lumina AI, I want the AI's product suggestions to respect my membership tier's price band, so that I receive affordable and relevant recommendations.

#### Acceptance Criteria

1. WHEN the chat AI generates product suggestions, THE Membership_System SHALL pass the current user's `Price_Band` maximum to the `ai_service.get_ai_response` function as a `price_ceiling` parameter.
2. WHEN product tags are resolved in `chat/views.py:_resolve_products`, THE Membership_System SHALL filter the resolved `Product` queryset to exclude products exceeding the user's `Price_Band` maximum.
3. WHILE a user is a Normal_Tier member, THE Membership_System SHALL include a context note in the AI system prompt indicating accessible (local and affordable) brand recommendations only.
4. WHILE a user is a Medium_Tier member, THE Membership_System SHALL include a context note in the AI system prompt indicating mid-range and exclusive pricing recommendations.
5. WHILE a user is a VIP_Tier member, THE Membership_System SHALL include a context note in the AI system prompt indicating highest-end brand recommendations.
6. IF the user's tier is undefined, invalid, or cannot be determined at request time, THE Membership_System SHALL default to Normal_Tier context behaviour and log a warning.

---

### Requirement 4: New Product Categories — Ayurvedic and Pharmacy

**User Story:** As a product manager, I want Ayurvedic and Pharmacy as recognised product ranges, so that these product types can be catalogued, filtered, and recommended correctly.

#### Acceptance Criteria

1. THE Membership_System SHALL add `('ayurvedic', 'Ayurvedic')` and `('pharmacy', 'Pharmacy')` to the `RANGE_CHOICES` field of the `Product` model in `apps/products/models.py`.
2. THE Membership_System SHALL create and apply a Django migration that adds `ayurvedic` and `pharmacy` as valid `product_range` values without altering existing data.
3. WHEN filtering products by `product_range=ayurvedic` or `product_range=pharmacy`, THE Membership_System SHALL return all products whose `product_range` matches the requested value as stored in the database, regardless of any data inconsistency in other fields.
4. THE Membership_System SHALL add sidebar navigation items for Ayurvedic and Pharmacy product ranges in `templates/base.html`, styled consistently with existing K-Beauty and Makeup sidebar items.

---

### Requirement 5: VIP 1:1 AI Doctor Consultation Page

**User Story:** As a VIP member, I want a private, dedicated AI Doctor consultation page, so that I can receive a one-on-one skin consultation experience separate from the general chat modes.

#### Acceptance Criteria

1. THE Membership_System SHALL create a dedicated URL `/doctor/` mapped to a new `doctor_consultation` view accessible only to VIP_Tier users.
2. WHEN a non-VIP user navigates to `/doctor/`, THE Membership_System SHALL redirect the user to a tier upgrade page with an informational message explaining the VIP requirement.
3. THE Membership_System SHALL create a new `Conversation` with `mode='doctor'` and a `is_vip_session=True` flag for each VIP user's Doctor Page session, or retrieve the user's existing active VIP Doctor session.
4. WHILE a VIP user is on the Doctor Page, THE Membership_System SHALL display the conversation history exclusively for that user's VIP Doctor sessions, not mixed with general doctor-mode conversations.
5. THE Membership_System SHALL apply a distinct visual gold accent theme (matching `--sb-gold: #c9a96e`) to the VIP Doctor Page as a permanent visual characteristic of the page, visible to any VIP user who accesses it.
6. IF the `Conversation` model does not yet have an `is_vip_session` boolean field, THE Membership_System SHALL add it via a new Django migration with a default of `False`.

---

### Requirement 6: Log & Earn Referral and Loyalty Programme

**User Story:** As a Normal or Medium tier user, I want to earn loyalty points by referring friends and completing purchases, so that I can redeem those points toward a tier upgrade.

#### Acceptance Criteria

1. THE Membership_System SHALL create a `ReferralLog` model with fields: `referrer` (FK to `UserProfile`), `referred_user` (FK to `UserProfile`), `points_awarded` (integer), `created_at` (datetime), and `status` (choices: `pending`, `confirmed`, `revoked`).
2. WHEN a new user registers using a valid `Referral_Code` in their signup form, THE Membership_System SHALL create a `ReferralLog` entry with `status='pending'`; THE Membership_System SHALL award `REFERRAL_POINTS` (default 100) to the referrer's `loyalty_points` when the referred user completes their first successful login.
3. WHEN a user completes an order in `apps/orders`, THE Membership_System SHALL award `PURCHASE_POINTS_RATE` points per ₹100 spent (default 1 point per ₹100) to the user's `loyalty_points`.
4. THE Membership_System SHALL provide a `/membership/redeem/` URL where users can spend `UPGRADE_POINTS_MEDIUM` points (default 500) to upgrade from Normal_Tier to Medium_Tier, or `UPGRADE_POINTS_VIP` points (default 1,500) to upgrade from Medium_Tier to VIP_Tier, supporting both upgrade paths.
5. WHEN a user redeems points for a tier upgrade, THE Membership_System SHALL deduct the required points from `loyalty_points`, set the new `tier`, set `tier_updated_at` to the current datetime, and create an audit log entry.
6. THE Membership_System SHALL display the user's current `loyalty_points` balance and a progress bar toward the next tier threshold on the user's `/me/` home page.
7. IF a `Referral_Code` submitted during registration does not match any existing `UserProfile.referral_code`, THE Membership_System SHALL reject the code silently and complete registration without awarding points.

---

### Requirement 7: Tier Upgrade Purchase Flow

**User Story:** As a Normal or Medium tier user, I want to purchase a tier upgrade with real payment, so that I can immediately access higher-tier features.

#### Acceptance Criteria

1. THE Membership_System SHALL provide a `/membership/upgrade/` page listing the Medium and VIP tier options with their prices, benefits, and a "Upgrade Now" call-to-action for each.
2. WHEN a user selects a tier upgrade and completes the payment step, THE Membership_System SHALL update `UserProfile.tier` to the purchased tier, set `subscription_expires_at` to 12 months from the current date, and record the transaction.
3. THE Membership_System SHALL send a confirmation email via the existing `EmailLog` mechanism in `apps/accounts` upon successful tier upgrade.
4. IF the user's current `tier` is already `vip`, THE Membership_System SHALL extend `subscription_expires_at` by 12 months rather than creating a duplicate upgrade.
5. WHERE payment integration is not yet configured, THE Membership_System SHALL accept a manual admin-override field on `UserProfile` (`admin_override_tier`, `admin_override_active` boolean) that supersedes the computed tier when `admin_override_active` is `True`.

---

### Requirement 8: Admin and Marketing Role Management

**User Story:** As an Admin or Marketing staff member, I want dedicated management views for tiers and promotions, so that I can oversee the membership system without relying on the Django admin panel.

#### Acceptance Criteria

1. THE Membership_System SHALL add a `staff_role` field to `UserProfile` with choices: `none`, `marketing`, `admin`; default `none`.
2. WHEN a user with `staff_role='admin'` accesses `/employee/memberships/`, THE Membership_System SHALL display a table of all users with their tier, `loyalty_points`, `referral_code`, and `subscription_expires_at`.
3. WHEN a user with `staff_role='admin'` changes a user's tier from the management table, THE Membership_System SHALL update `UserProfile.tier` and `tier_updated_at` and log the change.
4. WHEN a user with `staff_role='marketing'` accesses `/employee/memberships/`, THE Membership_System SHALL display the membership table in read-only mode without tier-edit controls, and IF the table cannot be displayed for any reason, THE Membership_System SHALL return a 403 Forbidden response to the marketing user.
5. IF a user without `staff_role='admin'` or `staff_role='marketing'` attempts to access `/employee/memberships/`, THE Membership_System SHALL return a 403 Forbidden response.

---

### Requirement 9: Sidebar Tier Badge and Access Gating

**User Story:** As a user, I want my membership tier shown in the sidebar and PRO-gated features visually marked, so that I can clearly see my access level and which features require an upgrade.

#### Acceptance Criteria

1. THE Membership_System SHALL replace the hardcoded `user.is_staff or user.username == 'suhani'` check in `templates/base.html` with a check against `user.profile.tier`.
2. WHEN a user's `tier` is `medium` or `vip`, THE Membership_System SHALL render the Makeup AI and K-Beauty AI sidebar items without the `PRO` badge.
3. WHEN a user's `tier` is `normal`, THE Membership_System SHALL render the Makeup AI and K-Beauty AI sidebar items with a `PRO` upgrade badge linking to `/membership/upgrade/`, regardless of whether those features are hidden or visible in the sidebar.
4. THE Membership_System SHALL render a `Tier_Badge` in the sidebar footer user card showing `FREE`, `PLUS`, or `VIP` in the corresponding tier colour (grey, teal, gold).
5. WHEN a VIP user is authenticated, THE Membership_System SHALL render an "AI Doctor (VIP)" sidebar item linking to `/doctor/` with a gold accent.

---

### Requirement 10: Animated UI Components

**User Story:** As a user, I want the Lumina interface to feel dynamic and engaging, so that browsing tiers, products, and chat feels visually alive rather than static.

#### Acceptance Criteria

1. THE Membership_System SHALL integrate the AOS (Animate On Scroll) library version 2.3.x into `templates/base.html` by adding the AOS stylesheet in the `<head>` block and the AOS initialisation script before `</body>`.
2. WHEN the membership tier upgrade page renders, THE Membership_System SHALL apply `data-aos="fade-up"` with staggered `data-aos-delay` values (0ms, 100ms, 200ms) to each tier card so they animate in sequentially using exactly the `fade-up` animation type; THE Membership_System SHALL NOT fall back to alternative animation types if `fade-up` is unavailable.
3. WHEN the product list page renders, THE Membership_System SHALL apply `data-aos="zoom-in"` to each product card.
4. THE Membership_System SHALL add a CSS keyframe animation `tier-glow` to `static/css/style.css` that pulses the gold border on VIP elements at a 2-second interval.
5. WHEN a tier upgrade is successfully completed, THE Membership_System SHALL trigger a full-screen confetti animation using a lightweight CSS-only or vanilla JS confetti effect (no additional npm dependencies) for 3 seconds before redirecting to the user's home page.
6. THE Membership_System SHALL add a hover lift effect (CSS `transform: translateY(-4px)` with `transition: transform 0.2s ease`) to all tier cards and product cards site-wide via `static/css/style.css`.

---

### Requirement 11: Round-Trip Tier Serialisation

**User Story:** As a developer, I want tier data to serialise and deserialise correctly, so that API responses, admin exports, and session data remain consistent.

#### Acceptance Criteria

1. THE Membership_System SHALL provide a `TierSerializer` that converts a `UserProfile` to a JSON-serialisable dictionary containing `tier`, `loyalty_points`, `referral_code`, and `subscription_expires_at`.
2. FOR ALL valid `UserProfile` instances, serialising then deserialising the result via `TierSerializer` SHALL produce a `UserProfile` state equivalent to the original (round-trip property).
3. WHEN `subscription_expires_at` is `None`, THE `TierSerializer` SHALL represent this field as `null` in serialised output and restore it as `None` on deserialisation.

