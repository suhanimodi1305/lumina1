# Design Document

## Overview

This document describes the technical architecture and design for migrating the Lumina beauty/skincare AI application from Django 4.2 / SQLite to a three-tier architecture:

- **Frontend**: Laravel Blade + Livewire 3 + Vue.js 3 + Tailwind CSS
- **Backend**: Laravel 12 (PHP 8.3) REST API + web server
- **AI Microservice**: Python 3.12 FastAPI (standalone process)
- **Database**: MySQL 8.0+ (multi-user, replacing SQLite)

The Django application continues to run until the migration is complete and verified.
The new stack is built alongside it; data is migrated in a single cutover step.

---

## Architecture

### System Topology

```
Browser
  │  HTTPS
  ▼
Nginx (reverse proxy + TLS termination)
  │
  ├──► PHP-FPM  ──► Laravel 12 App
  │                     │
  │              ┌──────┴──────────────┐
  │              │                     │
  │           MySQL 8             AI_Service
  │           (lumina_db)         (FastAPI / Uvicorn)
  │                                    │
  │                          ┌─────────┼──────────┐
  │                      Gemini AI  Grok-4    Groq Vision
  │
  └──► /media/** (served by Nginx directly)
```

- **Laravel** handles all web requests, authentication, business logic, and database writes.
- **AI_Service** is an internal-only FastAPI app reachable only from the Laravel host (localhost or private network). It wraps all AI/ML providers and the MediaPipe/OpenCV pipeline.
- **Nginx** terminates TLS, serves static assets and media files directly, and proxies everything else to PHP-FPM.
- **MySQL** replaces SQLite; all multi-user concurrency issues are solved at the DB layer.

---

## Components

### 1. Laravel Backend

| Concern | Implementation |
|---|---|
| Framework | Laravel 12 (PHP 8.3) |
| Auth | Laravel Sanctum (SPA + API tokens) + session |
| JWT (API) | `tymon/jwt-auth` for stateless token issuance |
| DB ORM | Eloquent ORM |
| Queue | Laravel Queue (database driver initially, Redis-upgradeable) |
| Mail | Laravel Mail (SMTP / Mailables) |
| File storage | Laravel Storage (local disk, `storage/app/private/`) |
| Config | `.env` via `vlucas/phpdotenv` (built into Laravel) |
| Rate limiting | Laravel's built-in `RateLimiter` facade (Redis-backed in production) |
| Middleware stack | `SecurityHeadersMiddleware`, `SessionExpiryMiddleware`, `TierExpiryMiddleware` |

**Key service classes:**

- `App\Services\AI\AiServiceClient` — HTTP client wrapping the FastAPI AI_Service
- `App\Services\Membership\TierService` — tier upgrade/downgrade/override logic
- `App\Services\Orders\CheckoutService` — transactional order creation + points award
- `App\Services\Scanner\ScanResultService` — persist ScanResult from AI payload
- `App\Services\Auth\EmailLogService` — record every outbound email to EmailLog

### 2. Python AI Microservice (FastAPI)

| Concern | Implementation |
|---|---|
| Framework | FastAPI 0.111+ |
| Server | Uvicorn (ASGI) |
| AI — face shape | xAI Grok-4 via OpenAI-compatible client; fallback: MediaPipe geometry |
| AI — skin analysis | Groq Llama-4-Scout Vision; fallback: OpenCV pixel analysis |
| AI — chat | Google Gemini 1.5 Pro (`google-generativeai`) |
| Face mesh | MediaPipe 0.10 (468 landmarks) |
| OpenCV | `opencv-python-headless` |
| Schema validation | Pydantic v2 models |
| Auth | Shared-secret API key in `Authorization: Bearer <key>` header |

**Endpoints:**

```
GET  /health          → {"status": "ok", "version": "..."}
POST /scan            → ScanResultSchema (JSON)
POST /chat            → {"response": "<assistant text>"}
```

**Scanner pipeline (ordered):**
```
receive image bytes
  → MIME validation (magic bytes)
  → MediaPipe: extract 468 face landmarks
      ↓ no face → raise NoFaceDetectedError
  → compute geometry measurements (6) and ratios (3)
  → Grok-4: classify face shape
      ↓ timeout / error → MediaPipe geometric classifier fallback
          ↓ also fails → OpenCV Canny edge classifier (confidence = 40)
  → Groq Llama-4-Scout Vision: acne / skin type / undertone / tone
      ↓ timeout / error → OpenCV pixel analysis fallback
  → assemble and return ScanResultSchema JSON
```

### 3. Frontend (Blade + Livewire + Vue.js)

| Concern | Implementation |
|---|---|
| Templates | Laravel Blade with component-based layout |
| Reactive UI | Livewire 3 (server-driven, AJAX-based) |
| Rich interactivity | Vue.js 3 (camera widget, chat thread) |
| Styling | Tailwind CSS 3 + custom design tokens |
| Build | Vite (bundler, replaces WhiteNoise) |
| Icons | Heroicons (SVG, Tailwind-compatible) |

**Page → component mapping:**

| Page | Livewire Component | Vue Component |
|---|---|---|
| Register / Login | `Auth\RegisterForm`, `Auth\LoginForm` | — |
| Dashboard | `Dashboard\DashboardPage` | — |
| Scanner | `Scanner\ScanUpload` | `ScanCamera.vue` |
| Scan result | `Scanner\ScanResultDetail` | — |
| Chat | `Chat\ChatPage` | `ChatThread.vue` |
| Products | `Products\ProductList`, `Products\ProductFilter` | — |
| Orders | `Orders\Checkout`, `Orders\OrderTracking` | — |
| Requirements | `Orders\RequirementForm` | — |
| Treatments | `Treatments\TreatmentList` | — |
| Employee mgmt | `Employee\EmployeeList`, `Employee\CsvImport` | — |
| Membership | `Memberships\TierStatus` | — |

### 4. MySQL Database

All tables use InnoDB engine, `utf8mb4_unicode_ci` collation, `BIGINT UNSIGNED` auto-increment PKs (except UUID PK tables), and `created_at` / `updated_at` timestamps managed by Eloquent.

---

## Data Models

### MySQL Schema (Eloquent models → tables)

```
users                        (Laravel default + staff_role column)
user_profiles                (tier, referral_code, loyalty_points, subscription_expires_at,
                              admin_override_tier, admin_override_active, tier_updated_at)
referral_logs                (referrer_id, referred_user_id, points_awarded, status)
tier_audit_logs              (profile_id, changed_by, previous_tier, new_tier,
                              points_deducted, reason)
email_logs                   (user_id, email_type, recipient, subject, body_preview,
                              status, error_msg, ip_address)

scan_results                 (user_id, session_key, is_demo, gender, scan_image,
                              skin_tone, undertone, face_shape, skin_type,
                              skin_age, real_age, harmony_score, hydration_score,
                              pigmentation_score, acne_score, aging_score, elasticity_score,
                              hf_acne_severity, hf_skin_type, hf_undertone,
                              hf_acne_confidence, hf_skin_type_confidence,
                              hf_undertone_confidence, facial_zones JSON,
                              face_shape_confidence, face_shape_reason,
                              face_shape_measurements JSON, face_shape_ratios JSON)
scan_result_skin_concerns    (pivot: scan_result_id, skin_concern_id)

conversations                (id UUID PK, user_id, title, mode, skin_scan_id, is_vip_session)
messages                     (id UUID PK, conversation_id, role, content, image_data)
quick_prompts                (prompt_text, category, order, active)

skin_concerns                (name, slug UNIQUE, description, icon)
products                     (name, brand, category, product_range, description,
                              key_ingredients, full_ingredients, price DECIMAL,
                              sku UNIQUE, image_url, suitable_for_skin_types JSON,
                              targets JSON, shades_available JSON,
                              undertone_match, skin_tone_match, coverage, finish, is_featured)

treatments                   (name, description, target_skin_concerns JSON,
                              applicable_skin_types JSON, is_active)

orders                       (order_id UNIQUE, tracking_id UNIQUE, user_id,
                              full_name, phone, email, address_line1, address_line2,
                              city, state, pincode, payment_method, payment_status,
                              status, subtotal, delivery_charge, discount, total,
                              estimated_delivery, delivered_at, order_notes)
order_items                  (order_id, product_id nullable, name, brand, image_url,
                              sku, shade, price DECIMAL, quantity)
order_status_logs            (order_id, status, message, location, timestamp)

user_requirements            (req_id UNIQUE, user_id, title, custom_product,
                              requirement_notes, quantity, priority,
                              full_name, phone, email, address_line1, address_line2,
                              city, state, pincode, status, assigned_to nullable,
                              employee_notes, linked_order_id nullable)
user_requirement_products    (pivot: user_requirement_id, product_id)

employee_login_logs          (user_id, event, ip_address, user_agent, session_key)
```

### Index Strategy

```sql
-- user lookups
CREATE INDEX idx_user_profiles_user_id       ON user_profiles(user_id);
CREATE INDEX idx_user_profiles_tier          ON user_profiles(tier);
CREATE INDEX idx_scan_results_user_id        ON scan_results(user_id);
CREATE INDEX idx_scan_results_created_at     ON scan_results(created_at);
CREATE INDEX idx_conversations_user_id       ON conversations(user_id);
CREATE INDEX idx_conversations_updated_at    ON conversations(updated_at);
CREATE INDEX idx_conversations_mode          ON conversations(mode);
CREATE INDEX idx_orders_user_id              ON orders(user_id);
CREATE INDEX idx_orders_status               ON orders(status);
CREATE INDEX idx_orders_created_at           ON orders(created_at);
CREATE INDEX idx_messages_conversation_id    ON messages(conversation_id);
CREATE INDEX idx_order_items_order_id        ON order_items(order_id);
CREATE INDEX idx_order_status_logs_order_id  ON order_status_logs(order_id);
```

---

## API Design

### Laravel REST Routes (prefix: `/api/v1`)

```
Auth
  POST   /auth/register
  POST   /auth/login
  POST   /auth/logout
  POST   /auth/password/email
  POST   /auth/password/reset

Memberships
  GET    /me                       (profile + tier)
  PATCH  /me                       (update profile)

Scanner
  POST   /scans                    (upload + run pipeline)
  GET    /scans                    (list user's scans)
  GET    /scans/{id}

Chat
  GET    /conversations
  POST   /conversations
  GET    /conversations/{id}
  POST   /conversations/{id}/messages

Products
  GET    /products                 (?skin_type=&undertone=&concern=&range=&category=&page=)
  GET    /products/{id}

Treatments
  GET    /treatments               (?scan_id=)

Orders
  POST   /orders                   (checkout)
  GET    /orders
  GET    /orders/{id}
  GET    /orders/track/{tracking_id}
  PATCH  /orders/{id}/status       (staff only)

Requirements
  POST   /requirements
  GET    /requirements
  GET    /requirements/{id}
  PATCH  /requirements/{id}/status (staff only)

Dashboard
  GET    /dashboard

Employee (staff only)
  GET    /employees
  POST   /employees/csv-import
  GET    /employees/login-logs
```

### AI Service Internal API

```
GET  /health
POST /scan          body: multipart/form-data { image: <file>, gender: str }
POST /chat          body: JSON {
                      conversation_history: [{role, content}],
                      mode: "ai_doctor"|"makeup"|"kbeauty",
                      tier: "normal"|"medium"|"vip",
                      scan_context?: {...},
                      image_base64?: "..."
                    }
```

---

## Security Design

### Middleware Stack (Laravel, order matters)

```
1. TrustProxies              — correct IP detection behind Nginx
2. HandleCors                — CORS policy for API routes
3. SecurityHeadersMiddleware — CSP, HSTS, X-Frame-Options, etc.
4. RateLimitMiddleware        — per-IP sliding window (Laravel RateLimiter)
5. EncryptCookies
6. AddQueuedCookiesToResponse
7. StartSession
8. SessionExpiryMiddleware    — 2-hour inactivity sliding window
9. AuthenticateWithSanctum   — JWT / session guard
10. TierExpiryMiddleware      — subscription expiry check + downgrade
11. VerifyCsrfToken           — 419 on missing/bad token
```

### Authentication Flow

```
Browser                Laravel                   MySQL
  │                       │                        │
  │── POST /auth/login ──►│                        │
  │                       │─ verify bcrypt hash ──►│
  │                       │◄─ User + UserProfile ──│
  │                       │─ issue JWT + session ──│
  │◄── 200 + JWT + cookie ─│
```

### MIME Validation (PHP)

```php
// First 16 bytes → detect real type
$bytes = substr(file_get_contents($path, false, null, 0, 16), 0, 16);
$allowed = [
    "\xFF\xD8\xFF" => 'jpeg',   // JPEG
    "\x89PNG\r\n"  => 'png',    // PNG
    "RIFF"         => 'webp',   // WebP (also needs bytes 8-11 = "WEBP")
];
```

### Immutable Log Protection

`TierAuditLog`, `OrderStatusLog`, and `EmployeeLoginLog` tables have no `updated_at` column. Their Eloquent models override `update()` and `delete()` to throw `ImmutableRecordException` (returns HTTP 403).

---

## Key Algorithms

### Tier Upgrade (TierService)

```
function checkAndUpgradeTier(UserProfile $profile):
  DB::transaction(function() use ($profile):
    $profile = UserProfile::lockForUpdate()->find($profile->id)
    $points  = $profile->loyalty_points
    $current = $profile->tier

    if current == 'normal' and points >= 1500:
        upgrade to 'vip', log TierAuditLog
    elif current == 'normal' and points >= 500:
        upgrade to 'medium', log TierAuditLog
    elif current == 'medium' and points >= 1500:
        upgrade to 'vip', log TierAuditLog
```

### Referral Points (atomic, idempotent)

```
function awardReferralPoints(User $referredUser):
  DB::transaction(function():
    $log = ReferralLog::where('referred_user_id', $referredUser->profile->id)
                      ->lockForUpdate()->first()
    if log.status == 'confirmed': return   // idempotency guard
    referrer_profile = lockForUpdate
    referrer_profile.loyalty_points += 100
    log.status = 'confirmed'
    log.points_awarded = 100
    TierService::checkAndUpgradeTier(referrer_profile)
```

### Order ID Generation

```php
function generateOrderId(): string
    $now    = now()->format('ymdHis')   // e.g. 250621143022
    $suffix = strtoupper(bin2hex(random_bytes(3)))  // 6 hex chars
    return "OD{$now}{$suffix}"
```

### Session Expiry Middleware

```php
function handle(Request $request, Closure $next):
    if skip_path($request): return $next($request)
    if !auth()->check(): return $next($request)

    $last = session('last_activity')
    if $last and (now()->timestamp - $last) > 7200:
        auth()->logout()
        session()->flush()
        return redirect('/login?expired=1')

    session(['last_activity' => now()->timestamp])
    return $next($request)
```

---

## Data Migration Plan (SQLite → MySQL)

A standalone PHP artisan command `migrate:from-sqlite` handles the one-time cutover:

```
Step 1  Disable FK checks in MySQL (SET FOREIGN_KEY_CHECKS=0)
Step 2  Migrate each table in dependency order:
          users → user_profiles → scan_results → conversations → messages
          → skin_concerns → products → treatments
          → orders → order_items → order_status_logs
          → user_requirements → referral_logs → tier_audit_logs
          → employee_login_logs → email_logs → quick_prompts
Step 3  Re-enable FK checks (SET FOREIGN_KEY_CHECKS=1)
Step 4  Verify FK integrity — abort + rollback on violation
Step 5  Row-count verification per table — abort + rollback on mismatch
Step 6  Log migration report (table name, source count, dest count, status)
```

JSON columns from SQLite (`facial_zones`, `suitable_for_skin_types`, `targets`, `shades_available`) are migrated as-is; MySQL stores them in native JSON columns.

---

## File Storage Layout

```
storage/
  app/
    private/
      scans/       {YYYY}/{MM}/{DD}/{uuid}.jpg   (scan images)
      csv/         {uuid}.csv                    (employee import, deleted after processing)
  public/          (symlinked to public/storage via php artisan storage:link)
```

Nginx serves `/storage/**` directly. Scan images are served via a signed URL generated by Laravel (`Storage::temporaryUrl()`).

---

## Environment Variables

### Laravel (.env)

```
APP_ENV=production
APP_KEY=
APP_URL=https://lumina.example.com

DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=lumina_db
DB_USERNAME=
DB_PASSWORD=

MAIL_HOST=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_FROM_ADDRESS=

AI_SERVICE_URL=http://127.0.0.1:8001
AI_SERVICE_SECRET=

SESSION_LIFETIME=120
SESSION_DRIVER=database

RATE_LIMITER_DRIVER=redis
REDIS_HOST=127.0.0.1
```

### AI Service (.env)

```
GEMINI_API_KEY=
GROK_API_KEY=
GROQ_API_KEY=
AI_SERVICE_SECRET=
PORT=8001
```

---

## Deployment

```
┌─ Server ──────────────────────────────────────────────────┐
│                                                           │
│  Nginx  :443 (TLS) ──────────────────────────────────────►│
│    │                                                       │
│    ├── /static/** ──► /var/www/lumina/public/             │
│    ├── /storage/** ──► storage/app/public/                │
│    └── /** ──────────► PHP-FPM :9000                      │
│                              │                            │
│                         Laravel 12                        │
│                              │                            │
│                    ┌─────────┴──────────┐                 │
│                  MySQL               AI_Service           │
│                  :3306             (Uvicorn :8001)        │
│                                                           │
└───────────────────────────────────────────────────────────┘
```

**Process management**: Supervisor manages both PHP-FPM and Uvicorn. Laravel queues run as a separate `artisan queue:work` supervisor job.

**Zero-downtime deploy**: Envoyer or a simple blue-green swap with `php artisan down` + migrate + `php artisan up`.
