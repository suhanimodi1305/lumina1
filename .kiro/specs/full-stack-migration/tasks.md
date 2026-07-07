# Implementation Plan

## Overview

This plan builds the Lumina full-stack migration in six phases, each phase unblocking the next.
Foundation tasks (1–3) establish the Laravel app, MySQL schema, and FastAPI skeleton.
Core backend tasks (4–6) layer authentication, membership logic, and the security middleware stack.
AI & Scanner tasks (7–8) complete the scan pipeline end-to-end.
Feature tasks (9–15) implement all ten application modules as REST API endpoints.
Frontend tasks (16–24) wire every module into Blade/Livewire/Vue pages.
Finally, migration and verification tasks (25–26) perform the SQLite cutover and validate all 19 requirements.

The Django application continues to run untouched until Task 25 is executed in the production cutover window.

---

## Tasks

### Phase 1 — Foundation

- [ ] 1. Project Scaffolding
  - Create a new Laravel 12 (PHP 8.3) application with full directory structure
  - Configure `.env` with all required variables: `APP_*`, `DB_*`, `MAIL_*`, `AI_SERVICE_*`, `SESSION_*`, `RATE_LIMITER_*`, `REDIS_*`
  - Add `.env` to `.gitignore`; commit only `.env.example` with placeholder values
  - Write Nginx virtual-host config: TLS termination, PHP-FPM proxy, `/storage/**` and `/static/**` direct serving
  - Run `php artisan storage:link` and verify symlink
  - Configure Supervisor unit files for PHP-FPM and `artisan queue:work`
  - Relevant Requirements: Requirement 19 (1, 3, 4, 6)

- [ ] 2. MySQL Schema and Eloquent Models
  - Depends on: Task 1
  - Create Laravel migrations for all tables in dependency order (users, user_profiles, referral_logs, tier_audit_logs, email_logs, skin_concerns, products, treatments, scan_results, scan_result_skin_concerns pivot, conversations UUID PK, messages UUID PK, quick_prompts, orders, order_items, order_status_logs, user_requirements, user_requirement_products pivot, employee_login_logs)
  - Apply all indexes from the design Index Strategy section
  - Generate Eloquent models with correct `$fillable`, casts, and relationships
  - Override `update()` and `delete()` on `TierAuditLog`, `OrderStatusLog`, and `EmployeeLoginLog` to throw `ImmutableRecordException` (HTTP 403)
  - Configure MySQL connection with READ COMMITTED isolation level and connection pool (min 2, max 10)
  - Relevant Requirements: Requirement 15 (5, 6, 7, 8), Requirement 2 (10), Requirement 6 (6), Requirement 10 (6)

- [ ] 3. Python FastAPI AI Microservice Skeleton
  - Scaffold FastAPI project: `main.py`, `routers/`, `schemas/`, `services/`, `middleware/`, `requirements.txt`
  - Implement `GET /health` returning `{"status": "ok", "version": "..."}` within 1 second
  - Implement shared-secret auth middleware: read `Authorization: Bearer <key>`, return HTTP 401 if absent or mismatched
  - Define all Pydantic v2 schemas: `ScanRequest`, `ScanResultSchema`, `ChatRequest`, `ChatResponse`, `HealthResponse`
  - Load all secrets from environment variables only (no hardcoding)
  - Configure Uvicorn startup on `127.0.0.1:8001`; add Supervisor unit
  - Relevant Requirements: Requirement 16 (1, 2, 3, 4, 5, 7, 8), Requirement 19 (2, 5)

### Phase 2 — Core Backend

- [ ] 4. User Authentication
  - Depends on: Task 2
  - Implement `POST /api/v1/auth/register`: validate email uniqueness, username uniqueness, password policy (≥8 chars, uppercase, lowercase, digit, special char); create `User` + `UserProfile` in one DB transaction; generate unique 10-char alphanumeric referral_code with retry loop
  - Implement `POST /api/v1/auth/login`: bcrypt verification (cost ≥12), issue JWT, set secure HttpOnly SameSite=Lax session cookie; respond within 500 ms
  - Implement `POST /api/v1/auth/logout`: invalidate session, clear cookie
  - Implement password reset flow: 60-minute expiry token, record to `EmailLog`, invalidate after use
  - HTTP 422 on duplicate fields; HTTP 401 on bad credentials (generic message, no field disclosure)
  - Wire `EmailLogService` to record every outbound email (type, recipient, subject, first 500 chars of body, status, IP)
  - Apply rate limiting: login 10 req/60 s, registration 5 req/60 s per IP (HTTP 429 on breach)
  - Relevant Requirements: Requirement 1 (1–10), Requirement 11 (1, 2, 4, 5), Requirement 18 (1)

- [ ] 5. Membership and Loyalty System
  - Depends on: Task 4
  - Implement `TierService::checkAndUpgradeTier()` with `SELECT FOR UPDATE`: Normal→Medium ≥500 pts, Normal/Medium→VIP ≥1500 pts (direct jump in one transaction); record `TierAuditLog`; update `tier_updated_at` to server UTC
  - Implement `GET /api/v1/me` and `PATCH /api/v1/me`
  - Implement referral point award with idempotency guard (check `ReferralLog.status` before awarding); award exactly 100 pts to referrer in same transaction; trigger tier check
  - Enforce price band ceilings per tier in product recommendation context
  - Implement admin override endpoints: set/unset `admin_override_active`; `effective_tier` always reflects override when active
  - Implement `TierExpiryMiddleware`: on every authenticated request check `subscription_expires_at < now()`; downgrade to Normal + record `TierAuditLog` if expired
  - Return HTTP 403 on any UPDATE or DELETE attempt on `TierAuditLog`
  - Relevant Requirements: Requirement 2 (1–11), Requirement 18 (3, 4)

- [ ] 6. Security Middleware Stack
  - Depends on: Task 4
  - Implement `SecurityHeadersMiddleware`: all required response headers (X-Content-Type-Options, X-XSS-Protection, Referrer-Policy, X-Frame-Options, Permissions-Policy, CSP on HTML, HSTS in production)
  - Implement `SessionExpiryMiddleware`: 7200 s sliding window; skip static paths; on expiry call `auth()->logout()`, flush session, redirect `/login?expired=1`; update `last_activity` on every non-skipped request
  - Implement PHP `MIME_Validator`: read first 16 magic bytes; allow JPEG/PNG/WebP for images; enforce 5 MB image limit and 1 MB CSV limit; reject with HTTP 422 before persistence; store accepted files with UUID v4 filename in non-public path
  - Configure `VerifyCsrfToken`: return HTTP 419 on missing/invalid token; session cookies `HttpOnly=true`, `SameSite=Lax`, `Secure=true` in production
  - Register all middleware in correct order per design document
  - Log CSRF failures, rate-limit breaches, and file-upload rejections to dedicated security audit log channel (WARNING+)
  - Relevant Requirements: Requirement 11 (1–5), Requirement 12 (1–6), Requirement 13 (1–5), Requirement 14 (1–5), Requirement 18 (1, 2, 5, 6)

### Phase 3 — AI & Scanner

- [ ] 7. FastAPI Scanner Pipeline
  - Depends on: Task 3
  - Implement `POST /scan` accepting `multipart/form-data` with `image` and `gender`
  - Pipeline in order: MIME validation → MediaPipe 468 landmarks (raise `no_face_detected` if no face) → compute 6 measurements + 3 ratios → Grok-4 face shape (10 s timeout → MediaPipe fallback → OpenCV Canny fallback, confidence=40) → Groq Llama-4-Scout Vision skin analysis (10 s timeout → OpenCV pixel fallback)
  - Return complete `ScanResultSchema` JSON with all fields from Requirement 3 AC 5; all scores 0–100 integers; exactly 5 facial zone objects
  - Complete within 30 s; return timeout error response if exceeded
  - Log provider errors (name, HTTP status, up to 200 chars of body); return structured error to caller
  - Enforce alphabetical key ordering on all JSON responses
  - Relevant Requirements: Requirement 3 (1, 3, 4, 5, 8, 10, 11, 12), Requirement 16 (1, 3, 6, 8)

- [ ] 8. Laravel Scanner Controller
  - Depends on: Task 6, Task 7
  - Apply `MIME_Validator` before processing: reject non-JPEG/PNG/WebP and files >5 MB without persisting
  - Apply rate limiting: scan upload 20 req/60 s per IP
  - Implement `AiServiceClient::scan()`: POST to AI service with auth header; relay `no_face_detected` to user without creating ScanResult; on timeout or non-2xx return HTTP 500 without returning unsaved results
  - On success: call `ScanResultService::persist()` in single DB transaction; store image at `storage/app/private/scans/{YYYY}/{MM}/{DD}/{uuid}.ext`; generate signed URL
  - Implement `GET /api/v1/scans` and `GET /api/v1/scans/{id}`
  - Return HTTP 500 if DB persistence fails; do not return AI results as if saved
  - Relevant Requirements: Requirement 3 (1, 2, 4, 6, 7, 9), Requirement 14 (1–5)

### Phase 4 — Features

- [ ] 9. AI Chat (Dr. Lumina)
  - Depends on: Task 3, Task 6, Task 8
  - Implement FastAPI `POST /chat`: accept up to 20 history messages + mode + tier + optional scan_context + optional image_base64; call Gemini 1.5 Pro; 10 s timeout → `{"error_code": "ai_timeout"}`; alphabetical JSON keys
  - Apply rate limiting: 60 req/60 s per IP
  - Implement Laravel: `POST /api/v1/conversations`, `GET /api/v1/conversations`, `GET /api/v1/conversations/{id}`, `POST /api/v1/conversations/{id}/messages`
  - Validate message ≤ 2000 chars; validate attached image (JPEG/PNG/WebP ≤5 MB) before calling AI
  - Persist user + assistant messages in single DB transaction
  - Apply tier-based system prompt rules (VIP context, Medium ≤₹2499, Normal ≤₹999); set `is_vip_session=true` for VIP
  - Store Conversation with UUID v4 PK, mode (ai_doctor/makeup/kbeauty), title (max 200 chars)
  - Relevant Requirements: Requirement 4 (1–11), Requirement 11 (1, 2), Requirement 16 (1, 3, 6, 8)

- [ ] 10. Product Catalogue
  - Depends on: Task 2
  - Implement `GET /api/v1/products` with filters: skin_type (contains value or "all"), undertone (equals or null/empty), concern (targets array exact slug match), product_range, category
  - Implement `GET /api/v1/products/{id}`; admin CRUD (staff-only)
  - Paginate: default 20/page; accept `page` and `per_page` (max 100); return empty array + `total=0` on no matches
  - Validate category against 35 enum values; validate product_range against 5 values
  - Ensure JSON array field round-trip fidelity
  - Relevant Requirements: Requirement 5 (1–8)

- [ ] 11. Orders and Checkout
  - Depends on: Task 5, Task 10
  - Apply rate limiting: 30 req/60 s per IP
  - Implement `POST /api/v1/orders`: validate address (full_name, phone, address_line1, city, state, pincode), payment method, ≥1 item; create Order + all OrderItems in single DB transaction; rollback entirely on any failure
  - Generate `order_id` as `OD{YYMMDDHHMMSS}{6-char CSPRNG uppercase hex}` (unique)
  - Generate `tracking_id` as 16-char cryptographically random URL-safe string (unique)
  - Snapshot product name/brand/image_url/SKU/price/shade onto OrderItem at creation
  - Enforce status sequence: pending→confirmed→packed→shipped→out_for_delivery→delivered; cancelled/returned reachable from any non-terminal; HTTP 422 on invalid transition
  - Append `OrderStatusLog` on each status change (message ≤300 chars, location ≤200 chars, server UTC); block UPDATE/DELETE on OrderStatusLog (HTTP 403)
  - Award `floor(total/100)` loyalty points in same transaction as "delivered" status update; trigger tier check
  - Implement `GET /api/v1/orders`, `GET /api/v1/orders/{id}`, `GET /api/v1/orders/track/{tracking_id}`, `PATCH /api/v1/orders/{id}/status` (staff only)
  - Relevant Requirements: Requirement 6 (1–11), Requirement 2 (8), Requirement 11 (1, 2), Requirement 18 (1)

- [ ] 12. User Requirements (Custom Product Requests)
  - Depends on: Task 4, Task 10
  - Implement `POST /api/v1/requirements`: validate title, address, quantity ≥1, and (catalogued product ID or non-empty custom_product); create record
  - Generate `req_id` as `REQ{YYMMDDHHMMSS}{6-char CSPRNG uppercase hex}` (unique)
  - Implement `PATCH /api/v1/requirements/{id}/status` (staff only — admin/marketing); store new status, actor ID, server UTC; HTTP 403 for non-staff
  - Enforce status machine: terminal statuses delivered/rejected/cancelled; HTTP 422 on transition from terminal
  - Store `linked_order_id` FK when requirement is fulfilled
  - Implement `GET /api/v1/requirements` and `GET /api/v1/requirements/{id}`
  - Relevant Requirements: Requirement 7 (1–6)

- [ ] 13. Treatment Recommendations
  - Depends on: Task 2, Task 8
  - Implement `GET /api/v1/treatments?scan_id=`: filter to active treatments whose `target_skin_concerns` contains ≥1 slug from ScanResult's detected concerns; if ScanResult has no concerns return all active; without scan_id return all `is_active=true`
  - Admin CRUD for treatments (staff-only)
  - Relevant Requirements: Requirement 8 (1–3)

- [ ] 14. User Dashboard
  - Depends on: Task 8, Task 9, Task 11
  - Implement `GET /api/v1/dashboard`: return in single response — top-10 ScanResults (created_at DESC) with thumbnail signed URL (null if no image), top-10 Conversations (updated_at DESC) with message count + last-message truncated to ≤100 chars + "…", top-10 Orders (created_at DESC) with item count (sum of quantities)
  - Guest scan history: `GET /api/v1/scans?session_key=` returns ScanResults for session key ordered by created_at DESC; empty array if none
  - Relevant Requirements: Requirement 9 (1–5)

- [ ] 15. Employee Management
  - Depends on: Task 4
  - On staff login: create `EmployeeLoginLog` (user_id, event="login", server UTC, client IP, user_agent ≤512 chars, session_key)
  - On staff logout: create `EmployeeLoginLog` (event="logout")
  - Block UPDATE/DELETE on `EmployeeLoginLog` (HTTP 403)
  - Implement `GET /api/v1/employees` and `GET /api/v1/employees/login-logs` (staff only; HTTP 403 for non-staff)
  - Implement `POST /api/v1/employees/csv-import`: validate CSV magic bytes + ≤1 MB (reject with "CSV file exceeds 1 MB limit"); process rows in single DB transaction; rollback all on any row failure, return HTTP 422 with row numbers + errors; store temp CSV as UUID filename; delete after processing
  - Relevant Requirements: Requirement 10 (1–6), Requirement 14 (1–5), Requirement 18 (1)

### Phase 5 — Frontend

- [ ] 16. Blade Layout, Tailwind CSS, and Vite Setup
  - Depends on: Task 1
  - Install and configure Tailwind CSS 3 via Vite (`vite.config.js`, `tailwind.config.js`, `postcss.config.js`)
  - Create base Blade layout with `@vite`, CSRF meta tag, Heroicons, `@livewireStyles` / `@livewireScripts`
  - Install Livewire 3 and Vue.js 3; wire together via Vite entry point
  - Define design tokens (colours, spacing, typography) in `tailwind.config.js`
  - Create shared Blade component files: button, input, alert, card
  - Remove all Bootstrap CSS/JS references
  - Verify WCAG 2.1 AA: contrast ≥4.5:1, keyboard navigation, ARIA labels
  - Relevant Requirements: Requirement 17 (1, 3, 6), Requirement 19 (3)

- [ ] 17. Auth Pages (Register, Login, Password Reset)
  - Depends on: Task 4, Task 16
  - Livewire components: `Auth\RegisterForm`, `Auth\LoginForm`, `Auth\PasswordResetRequest`, `Auth\PasswordResetForm`
  - Inline field-level validation errors without page reload on all auth forms
  - Include CSRF token; handle HTTP 419 → "Session expired" message + redirect to login
  - Relevant Requirements: Requirement 17 (1, 4, 7), Requirement 12 (5, 6)

- [ ] 18. Dashboard Page
  - Depends on: Task 14, Task 16
  - Livewire component `Dashboard\DashboardPage`: render three sections (scans, conversations, orders) from `GET /api/v1/dashboard`
  - Show tier badge and loyalty points; graceful empty-state for each section
  - Relevant Requirements: Requirement 9 (1–5), Requirement 17 (1, 4)

- [ ] 19. Scanner Page (Livewire + Vue.js Camera Widget)
  - Depends on: Task 8, Task 16
  - `ScanCamera.vue`: Vue.js 3 component using `getUserMedia`; capture still frame and emit blob to Livewire parent
  - Progress indicator on submit; 60 s timeout → dismiss indicator + show timeout error message
  - Render full scan result (face shape, skin metrics, scores, facial zones) on success
  - Relay `no_face_detected` as friendly user-facing message
  - Relevant Requirements: Requirement 3 (1, 2, 4, 5), Requirement 17 (1, 2, 4, 5), Requirement 12 (3)

- [ ] 20. Chat Page (Livewire + Vue.js Chat Thread)
  - Depends on: Task 9, Task 16
  - `ChatThread.vue`: message bubbles (user/assistant), auto-scroll, optional image attachment
  - Mode tabs: ai_doctor / makeup / kbeauty
  - Message input: textarea ≤2000 chars + optional image ≤5 MB (client-side pre-validation)
  - Handle AI timeout/error with user-facing error message; CSRF token in all requests; HTTP 419 redirect
  - Relevant Requirements: Requirement 4 (1–11), Requirement 17 (1, 2, 4, 7)

- [ ] 21. Products Page (Livewire Filters + Pagination)
  - Depends on: Task 10, Task 16
  - `Products\ProductList` + `Products\ProductFilter`: reactive filter panel (skin_type, undertone, concern, range, category); paginated product cards; empty state display
  - Relevant Requirements: Requirement 5 (2–7), Requirement 17 (1, 4)

- [ ] 22. Orders and Checkout Pages
  - Depends on: Task 11, Task 16
  - `Orders\Checkout`: address fields, payment method selector, order summary; inline validation; show order_id + tracking_id on success
  - `Orders\OrderTracking`: render OrderStatusLog timeline from `GET /api/v1/orders/track/{tracking_id}`
  - Order history list with status badge, total, estimated delivery
  - Relevant Requirements: Requirement 6 (1–11), Requirement 17 (1, 4)

- [ ] 23. Membership and Requirements Pages
  - Depends on: Task 5, Task 12, Task 16
  - `Memberships\TierStatus`: current tier, loyalty points, referral code, subscription expiry, admin override indicator
  - `Orders\RequirementForm`: submit custom product request; inline validation errors
  - Requirements history list with status badge and linked order
  - Relevant Requirements: Requirement 2 (1, 4, 5), Requirement 7 (1–6), Requirement 17 (1, 4)

- [ ] 24. Employee Management Pages
  - Depends on: Task 15, Task 16
  - `Employee\EmployeeList`: staff-only table; HTTP 403 redirect for non-staff
  - Login logs page: paginated EmployeeLoginLog entries
  - `Employee\CsvImport`: file upload ≤1 MB; row-level validation errors on failure; success count on completion
  - Relevant Requirements: Requirement 10 (1–6), Requirement 17 (1, 4)

### Phase 6 — Migration and Verification

- [ ] 25. SQLite to MySQL Data Migrator
  - Depends on: Task 2
  - Implement Artisan command `php artisan migrate:from-sqlite` (idempotent, rollback-safe)
  - Step 1: `SET FOREIGN_KEY_CHECKS=0`
  - Step 2: Migrate tables in dependency order (users → user_profiles → scan_results → conversations → messages → skin_concerns → products → treatments → orders → order_items → order_status_logs → user_requirements → referral_logs → tier_audit_logs → employee_login_logs → email_logs → quick_prompts)
  - Preserve original UUID values for Conversation.id and Message.id
  - Migrate JSON columns as-is into MySQL native JSON columns
  - Step 3: `SET FOREIGN_KEY_CHECKS=1`
  - Step 4: Verify FK integrity; on violation — report records, rollback all migrated data, exit non-zero
  - Step 5: Verify row counts per table; on mismatch — report discrepancy, rollback all, exit non-zero
  - Step 6: Print migration report (table, source count, dest count, status) to stdout and log file
  - Relevant Requirements: Requirement 15 (1–4)

- [ ] 26. End-to-End Testing and Verification
  - Depends on: Tasks 1–25
  - Write and run automated tests covering every acceptance criterion across all 19 requirements
  - Auth (Req 1): register, login, logout, JWT, bcrypt cost, duplicate 422, generic 401, reset expiry, EmailLog, rate limiting 429
  - Tiers (Req 2): tier upgrades, direct jump, override, deactivation, referral idempotency, order points, expiry downgrade, TierAuditLog immutability, referral code uniqueness
  - Scanner (Req 3): MIME reject, size reject, pipeline order, no-face response, schema completeness, DB transaction, 30 s timeout, all three fallbacks
  - Chat (Req 4): three modes, history truncation, Gemini timeout, message transaction, image validation, VIP flag, tier prompts, UUID v4 PK
  - Products (Req 5): all five filters, pagination cap, empty array
  - Orders (Req 6): transaction rollback, order_id format, tracking_id uniqueness, status sequence, 422 on skip, OrderStatusLog immutability, loyalty points in transaction, snapshot independence
  - Requirements (Req 7): req_id format, staff-only update, 403 non-staff, terminal status rejection, linked_order_id
  - Treatments (Req 8): concern filtering, empty-concern fallback, no-scan fallback
  - Dashboard (Req 9): ordering, thumbnail null, message truncation, guest session history
  - Employee (Req 10): log creation, CSV size limit, row rollback, staff guard, EmployeeLoginLog immutability
  - Rate limiting (Req 11): all five limits, 429, window reset, X-Forwarded-For extraction
  - Security headers (Req 12): all headers, CSP on HTML, HSTS in production, CSRF 419, secure cookies
  - Session expiry (Req 13): 2-hour window, redirect with expired=1, static path skip
  - File validation (Req 14): magic-byte rejection, no-persist, UUID filename
  - Migration (Req 15): row counts, FK integrity, UUID preservation, JSON fidelity
  - AI service (Req 16): health 200, Pydantic 422, 401 on bad key, alphabetical keys, round-trip fidelity
  - Frontend (Req 17): all 10 modules, Vue widgets, Tailwind (no Bootstrap), inline validation, scan timeout UI, WCAG contrast
  - Audit log (Req 18): all 8 event types, dedicated channel, no plaintext passwords/tokens
  - Deployment (Req 19): no secrets in source, Vite assets, PHP-FPM/Nginx, Uvicorn, HSTS max-age ≥31536000
  - Confirm all tests pass before marking complete
  - Relevant Requirements: Requirement 1–19 (all acceptance criteria)

---

## Task Dependency Graph

```json
{
  "waves": [
    { "wave": 1, "tasks": [1, 3] },
    { "wave": 2, "tasks": [2, 16] },
    { "wave": 3, "tasks": [4] },
    { "wave": 4, "tasks": [5, 6, 10, 25] },
    { "wave": 5, "tasks": [7] },
    { "wave": 6, "tasks": [8] },
    { "wave": 7, "tasks": [9, 11, 12, 13, 15] },
    { "wave": 8, "tasks": [14, 17] },
    { "wave": 9, "tasks": [18, 19, 20, 21, 22, 23, 24] },
    { "wave": 10, "tasks": [26] }
  ]
}
```

Key dependency chains:
- **Data layer**: 1 → 2 → (4, 10, 13, 25)
- **Auth & security**: 2 → 4 → 6 → (8, 9, 15)
- **AI pipeline**: 3 → 7 → 8 → (9, 14)
- **Business features**: 5, 10, 11, 12, 13, 14, 15 all depend on 2 + 4
- **Frontend**: 16 → (17–24), each page task depends on its backend API task
- **Verification**: 26 depends on all prior tasks

---

## Notes

- Tasks in the same wave can be worked in parallel.
- Task 3 (FastAPI skeleton) can be developed in parallel with Tasks 4–6 as it is a separate Python process.
- Task 6 (Security Middleware) must be complete before any file-upload or authenticated endpoint goes to QA.
- The Django app remains running and untouched until Task 25 cutover.
- Immutable log guards (`TierAuditLog`, `OrderStatusLog`, `EmployeeLoginLog`) must be in place from Task 2 onwards.
- All secrets must be read from environment variables only — never hardcoded.
