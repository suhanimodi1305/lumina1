# Requirements Document

## Introduction

This document specifies the requirements for migrating the **Lumina** beauty and skincare AI application
from its current Django 4.2 / SQLite / monolithic stack to a modern multi-tier architecture:

- **Frontend**: Laravel Blade + Livewire + Vue.js
- **Backend**: Laravel 12 (PHP) REST API
- **AI Microservice**: Python FastAPI (standalone, consumed by Laravel)
- **Database**: MySQL 8+ (replacing SQLite, supporting concurrent multi-user writes)
- **AI Models**: Gemini AI (chat), Grok-4/xAI (face shape), Groq Llama-4-Scout Vision (skin analysis), MediaPipe + OpenCV (face mesh geometry)

All ten existing application modules must be fully migrated with feature parity preserved and
all security controls re-implemented in the new stack.

---

## Glossary

- **Laravel_Backend**: The Laravel 12 PHP application serving the web frontend and REST API.
- **AI_Service**: The standalone Python FastAPI microservice that exposes AI/ML endpoints consumed by the Laravel_Backend.
- **Frontend**: The Laravel Blade + Livewire + Vue.js user interface layer.
- **MySQL_DB**: The MySQL 8+ relational database replacing SQLite.
- **Migrator**: The data migration tool/process that transfers existing SQLite records to MySQL_DB.
- **Scanner_Pipeline**: The sequential AI analysis pipeline (MediaPipe → Grok-4 → Groq Vision → OpenCV fallback).
- **ScanResult**: A stored skin and face analysis result associated with a user.
- **UserProfile**: The membership/tier record extending the base User account.
- **Conversation**: A chat session between a user and the Dr. Lumina AI, belonging to one mode.
- **Message**: An individual chat turn (user or assistant) within a Conversation.
- **Tier**: One of three membership levels — Normal, Medium, or VIP — governing feature access and price bands.
- **TierAuditLog**: An immutable record of every tier change event.
- **ReferralLog**: A record linking a referrer UserProfile to a referred UserProfile.
- **Order**: An e-commerce purchase record with line items, payment method, and status timeline.
- **OrderStatusLog**: An append-only timeline entry for an Order's status progression.
- **UserRequirement**: A custom product/service request submitted by a user and handled by staff.
- **EmployeeLoginLog**: An audit record of staff login and logout events.
- **EmailLog**: An audit record of every outbound transactional email.
- **Rate_Limiter**: The component enforcing per-IP request thresholds to prevent brute-force and DoS attacks.
- **Session_Manager**: The component that enforces server-side session expiry with a sliding-window timeout.
- **CSP**: Content Security Policy HTTP response header.
- **HSTS**: HTTP Strict Transport Security HTTP response header.
- **MIME_Validator**: The component that validates uploaded file content against allowed MIME types and magic bytes.
- **Connection_Pool**: The MySQL persistent connection pool managed by Laravel.
- **JWT**: JSON Web Token used for stateless API authentication between Frontend and Laravel_Backend.
- **PrettyPrinter**: The component that serialises internal data structures back to their canonical wire formats (JSON/API responses).

---

## Requirements

### Requirement 1: User Accounts and Authentication

**User Story:** As a user, I want to register, log in, reset my password, and manage my account,
so that my personal data and history are securely accessible across sessions.

#### Acceptance Criteria

1. WHEN a registration request is submitted with a valid email, username, and password that is at least 8 characters long and contains at least one uppercase letter, one lowercase letter, one digit, and one special character, THE Laravel_Backend SHALL create a new User record and UserProfile record in MySQL_DB within the same database transaction.
2. WHEN a registration request is submitted with a duplicate email or username, THE Laravel_Backend SHALL return a 422 response with a field-level validation error message identifying which field is duplicated.
3. WHEN valid credentials are submitted to the login endpoint, THE Laravel_Backend SHALL issue a signed JWT and set a secure HttpOnly session cookie within 500ms.
4. WHEN invalid credentials are submitted to the login endpoint, THE Laravel_Backend SHALL return a 401 response with a generic message that does not disclose whether the email or the password was incorrect.
5. WHEN a password reset is requested for a registered email address, THE Laravel_Backend SHALL send a time-limited (60-minute) reset link to that address and record the event in EmailLog.
6. WHEN a password reset link that has passed its 60-minute expiry is submitted, THE Laravel_Backend SHALL return a 422 response with an "expired token" error message and SHALL invalidate the token so it cannot be reused.
7. THE Laravel_Backend SHALL store all user passwords as bcrypt hashes with a cost factor of at least 12.
8. WHEN a user logs out, THE Laravel_Backend SHALL invalidate the server-side session and clear the session cookie.
9. THE Laravel_Backend SHALL record every outbound transactional email (type, recipient, subject, first 500 characters of body, status, IP address) in EmailLog.
10. WHEN the login endpoint receives more than 10 requests from the same IP address within 60 seconds, THE Rate_Limiter SHALL return HTTP 429 and SHALL NOT process further login attempts from that IP until the window resets.


### Requirement 2: Membership Tiers and Loyalty System

**User Story:** As a user, I want my membership tier (Normal / Medium / VIP) and loyalty points
to be tracked accurately, so that I receive the correct feature access and pricing benefits.

#### Acceptance Criteria

1. THE Laravel_Backend SHALL enforce three membership tiers — Normal, Medium, and VIP — each associated with a price band ceiling (Normal ≤ ₹999, Medium ≤ ₹2,499, VIP no ceiling).
2. WHEN a user's loyalty points reach or exceed 500 and the user's current tier is Normal, THE Laravel_Backend SHALL upgrade the UserProfile tier to Medium, update tier_updated_at to the current server UTC time, and record the change in TierAuditLog.
3. WHEN a user's loyalty points reach or exceed 1,500 and the current tier is Medium, THE Laravel_Backend SHALL upgrade the UserProfile tier to VIP, update tier_updated_at, and record the change in TierAuditLog; IF loyalty points jump from below 500 to ≥ 1,500 in a single transaction, THE Laravel_Backend SHALL upgrade directly to VIP and record one TierAuditLog entry.
4. WHEN an admin activates an override tier for a UserProfile, THE Laravel_Backend SHALL store the override tier and set admin_override_active to true; all subsequent requests for that UserProfile SHALL return the override tier as the effective tier until the override is deactivated.
5. WHEN an admin deactivates the override for a UserProfile, THE Laravel_Backend SHALL set admin_override_active to false and restore the effective tier to the UserProfile's base tier value.
6. WHEN a referred user completes their first successful authentication after registering with a valid referral code, THE Laravel_Backend SHALL award exactly 100 loyalty points to the referrer's UserProfile and create a confirmed ReferralLog entry within the same database transaction; subsequent logins by the same referred user SHALL NOT trigger additional point awards.
7. IF a referral code submitted at registration does not match any existing UserProfile.referral_code, THEN THE Laravel_Backend SHALL return a validation error identifying the invalid code and SHALL award no points.
8. WHEN a paid order is completed and the order total is ≥ ₹100, THE Laravel_Backend SHALL award floor(order_total / 100) loyalty points to the ordering user's UserProfile within the same transaction that marks the order as paid; IF the order total is < ₹100, THE Laravel_Backend SHALL award zero points.
9. WHEN an authenticated request is processed and the UserProfile's subscription_expires_at is earlier than the current server UTC time and the tier is not Normal, THE Laravel_Backend SHALL downgrade the tier to Normal, set tier_updated_at to the current server UTC time, and record the change in TierAuditLog before returning the response.
10. THE TierAuditLog SHALL be append-only; WHEN any request attempts to update or delete an existing TierAuditLog record, THE Laravel_Backend SHALL return a 403 response with an error message indicating the record is immutable.
11. WHEN a new UserProfile is created, THE Laravel_Backend SHALL generate the referral_code as a cryptographically random 10-character alphanumeric string and SHALL retry generation until a value unique across all existing UserProfile.referral_code values is obtained.


### Requirement 3: Face and Skin Scanner

**User Story:** As a user, I want to upload a photo and receive a detailed AI-powered skin and
face analysis, so that I can understand my skin condition and receive personalised recommendations.

#### Acceptance Criteria

1. WHEN a user uploads an image file, THE MIME_Validator SHALL inspect the first 16 magic bytes and reject any file whose detected type is not JPEG, PNG, or WebP, returning a validation error response before the Scanner_Pipeline is invoked.
2. WHEN an uploaded image exceeds 5 MB in size, THE MIME_Validator SHALL reject the file with a validation error response before the Scanner_Pipeline is invoked and SHALL NOT persist the file to disk.
3. WHEN a valid image is received, THE Scanner_Pipeline SHALL execute steps in this order: (a) MediaPipe 468-landmark face mesh extraction, (b) Grok-4 face shape classification from extracted measurements, (c) Groq Llama-4-Scout Vision skin attribute analysis.
4. WHEN MediaPipe detects no face in the uploaded image, THE AI_Service SHALL return a structured error response with error code "no_face_detected", and THE Laravel_Backend SHALL relay this error to the user without creating a ScanResult record.
5. WHEN the Scanner_Pipeline completes successfully, THE AI_Service SHALL return a JSON payload containing: face_shape, face_shape_confidence (0–100 integer), face_shape_reason, face_shape_measurements (exactly 6 numeric values), face_shape_ratios (exactly 3 numeric values), acne_severity (none/mild/moderate/severe), acne_confidence, skin_type, skin_type_confidence, undertone, undertone_confidence, skin_tone, facial_zones (exactly 5 named zone objects), visible_concerns (array), acne_score, hydration_score, pigmentation_score, aging_score, elasticity_score, harmony_score (all scores 0–100 integers).
6. WHEN THE Laravel_Backend receives a successful Scanner_Pipeline response, THE Laravel_Backend SHALL persist a ScanResult record linked to the authenticated user (or session key for guest users) in MySQL_DB within a single database transaction.
7. IF THE Laravel_Backend fails to persist the ScanResult record to MySQL_DB, THEN THE Laravel_Backend SHALL return a 500 error to the user and SHALL NOT return the AI analysis results as if they were saved.
8. THE AI_Service SHALL complete the full Scanner_Pipeline and return the JSON response to THE Laravel_Backend within 30 seconds of receiving the image; IF the pipeline does not complete within 30 seconds, THE AI_Service SHALL return a timeout error response.
9. THE PrettyPrinter SHALL serialise ScanResult records to JSON conforming to the schema in criterion 5; FOR ALL valid ScanResult records, serialising then deserialising SHALL produce an equivalent record where all named fields are present with values of the same type and content as the original.
10. IF the Grok-4 API fails to respond within 10 seconds or returns a non-2xx status, THEN THE Scanner_Pipeline SHALL fall back to MediaPipe's own geometric classifier for face shape classification and SHALL continue the remaining pipeline steps without returning an error to the user.
11. IF both Grok-4 and MediaPipe classifiers are unavailable, THEN THE Scanner_Pipeline SHALL use the OpenCV Canny edge geometry classifier and set face_shape_confidence to 40.
12. IF Groq Llama-4-Scout Vision fails to respond within 10 seconds or returns a non-2xx status, THEN THE Scanner_Pipeline SHALL use OpenCV pixel analysis as the fallback for skin attribute analysis and SHALL continue without returning an error to the user.


### Requirement 4: AI Chat Consultation (Dr. Lumina)

**User Story:** As a user, I want to consult with the Dr. Lumina AI in three specialised modes,
so that I receive personalised skin advice, makeup guidance, and K-Beauty routines.

#### Acceptance Criteria

1. THE Laravel_Backend SHALL support three chat modes: AI Doctor, Makeup, and K-Beauty; each mode SHALL use a distinct system prompt and persona stored in configuration.
2. WHEN a chat message of up to 2,000 characters is submitted, THE Laravel_Backend SHALL forward the last 20 messages of conversation history, the selected mode, the user's effective tier, and any linked ScanResult context to the AI_Service chat endpoint.
3. THE AI_Service SHALL call Gemini AI to generate the assistant response and return the response text to THE Laravel_Backend within 10 seconds; IF Gemini AI fails to respond within 10 seconds or returns an error, THE AI_Service SHALL return a structured error response with error code "ai_timeout" or "ai_error".
4. WHEN THE Laravel_Backend receives the assistant response, THE Laravel_Backend SHALL persist both the user Message and the assistant Message to the Conversation record in MySQL_DB within a single transaction.
5. WHEN a user submits an image alongside a chat message, THE Laravel_Backend SHALL validate the image using MIME_Validator (JPEG/PNG/WebP, ≤ 5 MB) before forwarding it to THE AI_Service; IF validation fails, THE Laravel_Backend SHALL return a validation error and SHALL NOT call THE AI_Service.
6. WHEN a user's effective tier is VIP, THE Laravel_Backend SHALL set the Conversation's is_vip_session flag to true and prepend the VIP tier context note to the system prompt.
7. WHEN a user's effective tier is Normal, THE Laravel_Backend SHALL prepend "Recommend products priced at ₹999 or below" to the product recommendation section of the system prompt.
8. WHEN a user's effective tier is Medium, THE Laravel_Backend SHALL prepend "Recommend products priced at ₹2,499 or below" to the product recommendation section of the system prompt.
9. THE Laravel_Backend SHALL store Conversation records with: UUID v4 primary key, user foreign key, mode (one of ai_doctor/makeup/kbeauty), title (max 200 characters), is_vip_session boolean, created_at, and updated_at timestamps.
10. WHEN a Conversation is created, THE Laravel_Backend SHALL assign a UUID v4 primary key; FOR ALL Conversations, the UUID SHALL be non-empty, globally unique across all Conversation records, and conform to the UUID v4 format (xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx).
11. THE AI_Service SHALL expose a POST /chat endpoint accepting: conversation_history (array of up to 20 message objects), mode (string), tier (string), optional scan_context (object), and optional image_base64 (string); the endpoint SHALL return the assistant response text as a JSON string field.


### Requirement 5: Product Catalogue

**User Story:** As a user, I want to browse and filter Korean skincare and makeup products by
category, skin type, undertone, and skin concern, so that I find products matched to my skin profile.

#### Acceptance Criteria

1. THE Laravel_Backend SHALL store products with the following attributes: name, brand, category (one of 35 defined enum values), product_range (one of: korean, makeup, treatment, ayurvedic, pharmacy), description, key_ingredients, full_ingredients, price (decimal), SKU (unique string), image_url, suitable_for_skin_types (JSON array of: oily, dry, combination, normal, all), targets (JSON array of concern slugs), shades_available (JSON array of shade objects with name and hex fields), undertone_match (one of: warm, cool, neutral, olive, or null/empty), skin_tone_match, coverage, finish, is_featured (boolean).
2. WHEN a product list request includes a skin_type filter, THE Laravel_Backend SHALL return only products whose suitable_for_skin_types array contains the requested skin_type value or the string "all".
3. WHEN a product list request includes an undertone filter, THE Laravel_Backend SHALL return only products whose undertone_match equals the requested undertone value or whose undertone_match is null or an empty string.
4. WHEN a product list request includes a concern filter, THE Laravel_Backend SHALL return only products whose targets array contains the requested concern slug as an exact string match.
5. WHEN a product list request includes a product_range filter, THE Laravel_Backend SHALL return only products whose product_range equals the requested value.
6. WHEN a product list request includes a category filter, THE Laravel_Backend SHALL return only products whose category equals the requested value.
7. THE Laravel_Backend SHALL return paginated product lists with a default page size of 20 items per page; the page and per_page query parameters SHALL be accepted, with per_page capped at 100; WHEN no products match the applied filters, THE Laravel_Backend SHALL return an empty items array with total count of 0.
8. THE PrettyPrinter SHALL serialise Product records to JSON; FOR ALL valid Product records, serialising then deserialising SHALL produce an equivalent record where every field has the same type and value as the original, including JSON array fields.


### Requirement 6: Orders and E-Commerce Checkout

**User Story:** As a user, I want to add products to a cart, place an order, pay via COD/UPI/card,
and track my order's delivery status, so that I can purchase Lumina products conveniently.

#### Acceptance Criteria

1. WHEN a checkout request is submitted with a valid delivery address (full_name, phone, address_line1, city, state, pincode), a supported payment method, and at least one order item, THE Laravel_Backend SHALL create an Order record and all associated OrderItem records within a single database transaction.
2. IF any step of the checkout transaction fails (validation error, DB write failure, payment gateway error), THEN THE Laravel_Backend SHALL roll back the entire transaction so no partial Order or OrderItem records remain in MySQL_DB.
3. THE Laravel_Backend SHALL generate each Order's order_id using the format OD{YYMMDDHHMMSS}{6-char uppercase hex suffix} where the suffix is produced by a cryptographically secure random number generator; the resulting order_id SHALL be unique across all Order records.
4. THE Laravel_Backend SHALL generate each Order's tracking_id as a 16-character cryptographically random URL-safe string unique across all Order records.
5. WHEN an order's status is updated, THE Laravel_Backend SHALL append a new OrderStatusLog entry containing: new status, descriptive message (max 300 characters), optional location (max 200 characters), and server UTC timestamp.
6. THE Laravel_Backend SHALL NOT permit modification or deletion of existing OrderStatusLog entries; WHEN any such request is received, THE Laravel_Backend SHALL return a 403 response.
7. WHEN loyalty points are awarded upon order completion, THE Laravel_Backend SHALL execute the point credit and the order status update to "delivered" within the same database transaction.
8. THE Laravel_Backend SHALL support the following payment methods: cod, upi, card, netbanking, wallet.
9. THE Laravel_Backend SHALL enforce order status transitions in the sequence: pending → confirmed → packed → shipped → out_for_delivery → delivered; the terminal statuses cancelled and returned SHALL be reachable from any non-terminal status; THE Laravel_Backend SHALL reject any transition that skips a step in the sequence and return a 422 error.
10. WHEN an OrderItem is created, THE Laravel_Backend SHALL snapshot and store the product's name, brand, image_url, SKU, price, and shade at the time of order creation; subsequent edits to the source Product record SHALL NOT alter the stored OrderItem snapshot values.
11. FOR ALL valid Order records, serialising then deserialising the order (including all OrderItems and OrderStatusLog entries) as JSON SHALL produce an equivalent record where every field has the same type and value as the original.


### Requirement 7: User Requirements (Custom Product Requests)

**User Story:** As a user, I want to submit custom product requests that staff can fulfil,
so that I can obtain products not currently in the catalogue.

#### Acceptance Criteria

1. WHEN a UserRequirement is submitted with a title, valid delivery address (full_name, phone, address_line1, city, state, pincode), quantity ≥ 1, and either at least one catalogued product ID or a non-empty custom_product description, THE Laravel_Backend SHALL create the UserRequirement record in MySQL_DB.
2. THE Laravel_Backend SHALL generate each UserRequirement's req_id using the format REQ{YYMMDDHHMMSS}{6-char uppercase hex suffix} with a cryptographically secure random suffix, unique across all UserRequirement records.
3. WHEN a user with staff_role "admin" or "marketing" updates the status of a UserRequirement, THE Laravel_Backend SHALL store the new status, the updating user's ID, and a server UTC timestamp on the UserRequirement record.
4. WHEN a non-staff user attempts to update the status of a UserRequirement, THE Laravel_Backend SHALL return a 403 response.
5. WHEN a UserRequirement is linked to an Order, THE Laravel_Backend SHALL store the Order's primary key as a foreign key on the UserRequirement record.
6. THE Laravel_Backend SHALL support the following UserRequirement statuses: pending, accepted, processing, dispatched, delivered, rejected, cancelled; the terminal statuses are delivered, rejected, and cancelled; THE Laravel_Backend SHALL reject status transitions from terminal statuses and return a 422 error.


### Requirement 8: Treatment Recommendations

**User Story:** As a user, I want to receive treatment recommendations based on my scan results,
so that I know which Lumina treatments address my detected skin concerns.

#### Acceptance Criteria

1. WHEN a ScanResult is referenced in a treatment list request, THE Laravel_Backend SHALL return only active treatments whose target_skin_concerns array contains at least one concern slug that also appears in the ScanResult's detected_concerns; IF the ScanResult has no detected concerns, THE Laravel_Backend SHALL return all active treatments.
2. THE Laravel_Backend SHALL store treatment records with: name (string), description (text), target_skin_concerns (JSON array of concern slugs), applicable_skin_types (JSON array), and is_active (boolean, default true).
3. WHEN a treatment list request is made without a ScanResult reference, THE Laravel_Backend SHALL return all treatments where is_active is true, without concern-based filtering.


### Requirement 9: User Dashboard

**User Story:** As a user, I want a personal dashboard showing my scan history, chat history,
and order history, so that I can review my Lumina activity in one place.

#### Acceptance Criteria

1. WHEN an authenticated user requests their dashboard, THE Laravel_Backend SHALL return the user's 10 most recent ScanResult records (ordered by created_at DESC), 10 most recent Conversation records (ordered by updated_at DESC), and 10 most recent Order records (ordered by created_at DESC) in a single response.
2. WHEN a guest user (unauthenticated, identified by session key) requests scan history, THE Laravel_Backend SHALL return ScanResult records linked to that session key ordered by created_at DESC; IF no records exist for the session key, THE Laravel_Backend SHALL return an empty array.
3. THE Laravel_Backend SHALL include in each dashboard ScanResult entry: created_at date, skin_tone, undertone, skin_type, face_shape, acne_severity (hf_acne_severity), harmony_score, and a thumbnail URL pointing to the stored scan_image path; IF scan_image is null, the thumbnail URL SHALL be null.
4. THE Laravel_Backend SHALL include in each dashboard Conversation entry: title, mode, message count, last message content truncated to ≤ 100 characters with "…" appended if truncated, and updated_at timestamp.
5. THE Laravel_Backend SHALL include in each dashboard Order entry: order_id, total (decimal), status, estimated_delivery (date or null), and item count (sum of OrderItem quantities).


### Requirement 10: Employee Management

**User Story:** As an administrator, I want to manage staff accounts, view login logs, and
bulk-import employees from CSV, so that employee access is auditable and easy to maintain.

#### Acceptance Criteria

1. WHEN a user whose staff_role is "admin" or "marketing" successfully authenticates, THE Laravel_Backend SHALL create an EmployeeLoginLog record containing: user ID, event type "login", server UTC timestamp, client IP address, user agent string (max 512 characters), and session key.
2. WHEN a staff user logs out, THE Laravel_Backend SHALL create an EmployeeLoginLog record with event type "logout", user ID, server UTC timestamp, and session key.
3. WHEN a bulk CSV upload is submitted, THE Laravel_Backend SHALL check the file size before processing any rows; IF the file size exceeds 1 MB, THEN THE Laravel_Backend SHALL return a 422 error with message "CSV file exceeds 1 MB limit" and SHALL NOT process any rows.
4. WHEN a valid CSV file is processed, THE Laravel_Backend SHALL create or update employee User records for each valid row within a single database transaction; IF any row fails validation, THE Laravel_Backend SHALL roll back all row inserts/updates and return a 422 response listing the failing row numbers and error messages.
5. THE Laravel_Backend SHALL enforce that only authenticated users with staff_role "admin" or "marketing" can access employee management endpoints; WHEN a user without this role attempts access, THE Laravel_Backend SHALL return a 403 response.
6. THE EmployeeLoginLog SHALL be append-only; WHEN any request attempts to update or delete an existing EmployeeLoginLog record, THE Laravel_Backend SHALL return a 403 response with an error message indicating the record is immutable.


### Requirement 11: Security — Rate Limiting

**User Story:** As a system operator, I want per-IP rate limiting on sensitive endpoints,
so that brute-force and DoS attacks are mitigated.

#### Acceptance Criteria

1. THE Rate_Limiter SHALL enforce the following per-IP sliding-window limits: login — 10 requests per 60 seconds; registration — 5 requests per 60 seconds; scan upload — 20 requests per 60 seconds; chat messages — 60 requests per 60 seconds; orders — 30 requests per 60 seconds.
2. WHEN a client's request count for a protected endpoint exceeds the configured limit within the sliding window, THE Rate_Limiter SHALL return an HTTP 429 response and SHALL NOT process the request.
3. WHEN the rate limit window expires for a client IP on a given endpoint, THE Rate_Limiter SHALL reset the request count to zero and allow new requests.
4. THE Rate_Limiter SHALL extract the client IP from the X-Forwarded-For header when present (using the rightmost non-private IP), or from REMOTE_ADDR when X-Forwarded-For is absent.
5. THE Rate_Limiter SHALL operate independently per endpoint prefix; a limit exceeded on the login endpoint SHALL NOT affect the rate limit counter for the scan endpoint.


### Requirement 12: Security — HTTP Headers and CSRF Protection

**User Story:** As a system operator, I want all HTTP responses to include hardening security headers
and all state-changing requests to be CSRF-protected, so that common web attack vectors are mitigated.

#### Acceptance Criteria

1. THE Laravel_Backend SHALL include the following headers on every HTTP response: X-Content-Type-Options: nosniff, X-XSS-Protection: 1; mode=block, Referrer-Policy: strict-origin-when-cross-origin, X-Frame-Options: DENY.
2. THE Laravel_Backend SHALL include a Content-Security-Policy header on every HTML response restricting default-src to 'self', with explicit allowlists for any CDN script and style sources used by the application.
3. THE Laravel_Backend SHALL include a Permissions-Policy header on every response denying access to geolocation, microphone, payment, USB, magnetometer, and gyroscope; the camera permission SHALL be omitted from the deny list to permit getUserMedia on the scan page.
4. WHEN the application is running with APP_ENV=production, THE Laravel_Backend SHALL include Strict-Transport-Security: max-age=31536000; includeSubDomains; preload on every HTTPS response.
5. THE Laravel_Backend SHALL generate and validate CSRF tokens for all POST, PUT, PATCH, and DELETE requests from browser clients; WHEN a CSRF token is absent or invalid, THE Laravel_Backend SHALL return a 419 response.
6. THE Laravel_Backend SHALL set session cookies with HttpOnly=true, SameSite=Lax, and Secure=true when APP_ENV=production.


### Requirement 13: Security — Session Expiry

**User Story:** As a system operator, I want authenticated sessions to expire after 2 hours of
inactivity using a sliding window, so that unattended sessions cannot be hijacked.

#### Acceptance Criteria

1. THE Session_Manager SHALL enforce a 2-hour (7,200-second) inactivity timeout using a sliding window; WHEN an authenticated request is processed, THE Session_Manager SHALL reset the inactivity timer.
2. WHEN the inactivity period elapses without a request from an authenticated user, THE Session_Manager SHALL invalidate the server-side session on the next request from that user and redirect the user to the login page with an "expired=1" query parameter.
3. THE Session_Manager SHALL skip the expiry check for requests to static asset paths (/css/, /js/, /images/, /media/) and the session-ping endpoint.
4. WHEN a session expires, THE Session_Manager SHALL call the framework's logout method and flush all session data before issuing the redirect.
5. WHILE a user is authenticated and the session is active, THE Session_Manager SHALL store the last_activity timestamp server-side and update it on every non-skipped request.


### Requirement 14: Security — File Upload Validation

**User Story:** As a system operator, I want all file uploads to be validated for type and size
before processing, so that malicious files cannot enter the system.

#### Acceptance Criteria

1. WHEN a file is uploaded to any endpoint, THE MIME_Validator SHALL inspect the file's first 16 magic bytes to determine the actual content type, independent of the client-reported Content-Type header.
2. WHEN the magic-byte-detected type is not in the allowed list (JPEG, PNG, WebP for scan/chat images; CSV for bulk employee import), THE MIME_Validator SHALL reject the file with a 422 response identifying the rejection reason and SHALL NOT persist the file to disk.
3. WHEN an image file's size exceeds 5 MB, THE MIME_Validator SHALL reject the file with a 422 response and SHALL NOT persist the file to disk.
4. WHEN a CSV file's size exceeds 1 MB, THE MIME_Validator SHALL reject the file with a 422 response and SHALL NOT persist the file to disk.
5. WHEN a file passes all MIME_Validator checks, THE Laravel_Backend SHALL store the file in a directory not directly accessible via a public URL, using a UUID v4-based filename that discards the original client-provided filename.


### Requirement 15: Database Migration — SQLite to MySQL

**User Story:** As a system operator, I want all existing SQLite data migrated to MySQL with
integrity and concurrency support, so that no historical records are lost during the stack transition.

#### Acceptance Criteria

1. THE Migrator SHALL transfer all records from the following SQLite tables to the corresponding MySQL_DB tables without data loss: users, user_profiles, referral_logs, tier_audit_logs, scan_results, conversations, messages, quick_prompts, products, skin_concerns, orders, order_items, order_status_logs, user_requirements, treatments, employee_login_logs, email_logs.
2. WHEN migrating records with UUID primary keys (Conversation, Message), THE Migrator SHALL preserve the original UUID values unchanged in MySQL_DB.
3. THE Migrator SHALL enforce foreign key constraint checks in MySQL_DB after all records are loaded; IF any foreign key violation is found, THEN THE Migrator SHALL report the violating records, roll back all migrated data, and leave MySQL_DB in its pre-migration state.
4. THE Migrator SHALL verify that the row count for each migrated table in MySQL_DB equals the corresponding row count in SQLite after migration; IF any count does not match, THEN THE Migrator SHALL report the discrepancy, roll back all migrated data, and leave MySQL_DB in its pre-migration state.
5. THE MySQL_DB schema SHALL define explicit indexes on all foreign key columns and on the following query-critical columns: users.id, user_profiles.tier, scan_results.created_at, orders.status, conversations.mode, conversations.updated_at.
6. THE Connection_Pool SHALL maintain a minimum of 2 and a maximum of 10 persistent MySQL connections per Laravel worker process.
7. THE Laravel_Backend SHALL use MySQL transaction isolation level READ COMMITTED for all write transactions to prevent dirty reads while allowing concurrent reads.
8. WHEN two concurrent requests attempt to write to the same UserProfile row (e.g., simultaneous loyalty point updates), THE Laravel_Backend SHALL acquire a SELECT FOR UPDATE lock on that row before writing to serialise the writes and prevent lost updates.


### Requirement 16: AI Microservice Architecture (FastAPI)

**User Story:** As a system operator, I want the Python AI/ML logic exposed as a standalone
FastAPI microservice, so that it can be independently scaled, deployed, and consumed by Laravel.

#### Acceptance Criteria

1. THE AI_Service SHALL expose the following REST endpoints: POST /scan (image analysis pipeline), POST /chat (Gemini AI conversation turn), GET /health (service liveness check).
2. WHEN THE AI_Service receives a GET /health request, THE AI_Service SHALL return HTTP 200 with a JSON body confirming service status within 1 second.
3. THE AI_Service SHALL validate all incoming request payloads against defined Pydantic schemas and return HTTP 422 with field-level error details for any invalid input.
4. THE Laravel_Backend SHALL authenticate every request to THE AI_Service using a shared-secret API key in the Authorization header; WHEN the key is absent or invalid, THE AI_Service SHALL return HTTP 401.
5. THE AI_Service SHALL NOT expose any endpoint directly to the public internet; all AI_Service endpoints SHALL be network-accessible only from the Laravel_Backend host.
6. WHEN THE AI_Service calls an external AI provider (Gemini, Grok-4, Groq) and the provider returns an error, THE AI_Service SHALL log the provider name, HTTP status code, and up to 200 characters of the response body, and SHALL return a structured error response to THE Laravel_Backend.
7. THE AI_Service SHALL be implemented in Python using FastAPI and SHALL run as a separate OS process from THE Laravel_Backend.
8. WHEN THE AI_Service serialises a response object to JSON, it SHALL order all top-level keys alphabetically; FOR ALL valid AI_Service response objects, serialising then deserialising SHALL produce an object where every field has the same type and value as the original.


### Requirement 17: Frontend — Laravel Blade / Livewire / Vue.js

**User Story:** As a user, I want a responsive, modern web interface for all Lumina features,
so that I can use the application comfortably on desktop and mobile browsers.

#### Acceptance Criteria

1. THE Frontend SHALL implement all ten feature modules (Accounts, Memberships, Scanner, Chat, Products, Orders, Treatments, Dashboard, Employee, Core) as Blade views with Livewire components handling reactive UI behaviour.
2. THE Frontend SHALL use Vue.js components for the scanner camera-capture widget and the chat message thread where real-time reactivity is required.
3. THE Frontend SHALL replace all Bootstrap 5 styles with Tailwind CSS; custom component classes SHALL be defined in dedicated Blade component files.
4. WHEN a Livewire component action fails validation, THE Frontend SHALL display field-level error messages inline adjacent to the relevant inputs without a full page reload.
5. WHEN a user submits the scan upload form, THE Frontend SHALL display a progress indicator; IF the Scanner_Pipeline does not return a response within 60 seconds, THE Frontend SHALL dismiss the indicator and display a timeout error message.
6. THE Frontend SHALL meet WCAG 2.1 Level AA on all pages, including colour contrast ratios ≥ 4.5:1 for normal text, full keyboard navigation, and ARIA labels on all interactive elements.
7. THE Frontend SHALL include a valid CSRF token in every Livewire and Vue.js AJAX request; WHEN a 419 response is received, THE Frontend SHALL display a "Session expired — please log in again" message and redirect to the login page.


### Requirement 18: Audit Logging

**User Story:** As a system operator, I want security-relevant events written to an audit log,
so that suspicious activity can be detected and investigated.

#### Acceptance Criteria

1. THE Laravel_Backend SHALL write a log entry — including UTC timestamp and affected user ID — for each of the following events: user login (success and failure), user logout, failed CSRF validation, rate limit exceeded, file upload rejection, tier change, password reset request, admin override activation/deactivation.
2. WHEN a rate limit exceeded event is logged, THE Laravel_Backend SHALL include: client IP, endpoint path, request count, and window duration in seconds.
3. WHEN a tier change event is logged, THE Laravel_Backend SHALL include: user ID, previous tier, new tier, reason, and the identity of the actor (user ID or "system").
4. WHEN an admin override activation or deactivation event is logged, THE Laravel_Backend SHALL include: admin user ID, target user ID, override tier value, and the action taken (activated/deactivated).
5. THE Laravel_Backend SHALL write all security audit log entries to a dedicated log channel (separate from the application log) at level WARNING or higher.
6. THE Laravel_Backend SHALL NOT include plaintext passwords, full session tokens, or unmasked payment card numbers in any log entry.


### Requirement 19: Deployment Configuration

**User Story:** As a system operator, I want the migrated application deployed with a clean
separation of concerns and environment-based configuration, so that secrets are not exposed
and the production environment is reproducible.

#### Acceptance Criteria

1. THE Laravel_Backend SHALL read all secrets (database credentials, API keys, SMTP credentials, AI service shared secret) exclusively from environment variables; secret values SHALL NOT appear in any source-controlled file, and the .env file SHALL be listed in .gitignore.
2. THE AI_Service SHALL read all secrets (Gemini API key, Grok-4 API key, Groq API key, shared internal API key) exclusively from environment variables.
3. THE Laravel_Backend SHALL serve compiled static assets using Laravel Vite; WhiteNoise SHALL NOT be used in the new stack.
4. THE Laravel_Backend SHALL run under PHP-FPM behind Nginx or Apache; Gunicorn SHALL NOT be used for the Laravel_Backend.
5. THE AI_Service SHALL run under Uvicorn (or Gunicorn with Uvicorn workers) as its ASGI server.
6. WHEN APP_ENV is set to "production", THE Laravel_Backend SHALL disable all debug output, enforce HTTPS redirects, and set HSTS with a max-age of at least 31536000 seconds.
