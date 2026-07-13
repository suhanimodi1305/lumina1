# LUMINA AI — COMPLETE SYSTEM DESIGN

## 🏗️ Architecture Overview

Lumina AI is a Django-based beauty-tech platform that combines AI skin analysis, personalized skincare recommendations, e-commerce, progress tracking, and membership tiers.

**Tech Stack:**
- **Backend:** Django 4.2 (Python)
- **Database:** SQLite (dev), PostgreSQL-ready
- **AI Services:** 
  - Groq API (llama-3.3-70b) — Chat consultants
  - HuggingFace APIs — Skin analysis
  - xAI Grok — Face shape detection
- **Frontend:** Bootstrap 5 + Vanilla JS
- **Payment:** Not yet integrated (admin override for tiers)

---

## 📊 System Flow Diagrams

### PAGE 1: COMPLETE SYSTEM OVERVIEW

```
┌──────────────────────────────────────────────────────────┐
│                    PUBLIC WEBSITE                        │
│  Home │ AI Scan │ Products │ Blog │ Community │ Login   │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│                  USER APPLICATION                        │
│  Dashboard │ Face Scan │ AI Report │ Routine │ Progress │
│  Orders │ Rewards │ Profile │ Weekly Check-in │ Chat AI │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│                     AI ENGINE                            │
│  Vision AI │ Smart Quiz │ Recommendation │ Chat AI     │
│  Progress Analysis │ Routine Generator                  │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│                     DATABASE                             │
│  Users │ Scans │ Products │ Orders │ Progress │ Reviews │
│  Coupons │ Notifications │ Blog Posts                  │
└──────────────────────────────────────────────────────────┘
                          ↓
┌──────────────────────────────────────────────────────────┐
│                    ADMIN PANEL                           │
│  Users │ Products │ Orders │ AI │ Marketing │ Reports   │
│  Memberships │ Reviews │ Blog │ Coupons                │
└──────────────────────────────────────────────────────────┘
```

### PAGE 2: USER JOURNEY FLOW

```
Landing Page
    ↓
Register/Login
    ↓
AI Face Scan (upload selfie)
    ↓
AI Face Validation
    ↓
AI Face Analysis (HuggingFace + xAI)
    ↓
Smart Questionnaire (11 sections, ~40 questions)
    ↓
AI Analysis Report
    ↓
Morning & Night Routine
    ↓
Product Recommendations
    ↓
Dashboard
    ↓
Daily Routine Tracking
    ↓
Weekly Check-in (every 7 days)
    ↓
14-Day Progress Scan
    ↓
AI Comparison Report
    ↓
30/60/90 Day Milestones
    ↓
Transformation Report
```

### PAGE 3: AI ENGINE FLOW

```
Upload Selfie
    ↓
Image Validation (size, type, magic bytes)
    ↓
Face Detection (MediaPipe)
    ↓
AI Analysis Pipeline:
    ├── HF: Acne Severity Detection
    ├── HF: Skin Type Classification
    ├── HF: Undertone Detection
    ├── xAI Grok: Face Shape Classification
    └── OpenCV: Skin Tone Mapping
    ↓
Score Calculation:
    ├── Harmony Score (0-100)
    ├── Hydration Score
    ├── Pigmentation Score
    ├── Acne Score
    ├── Aging Score
    └── Elasticity Score
    ↓
Smart Questionnaire Analysis
    ↓
History Analysis (if previous scans exist)
    ↓
Recommendation Engine:
    ├── Ingredient Recommendations
    ├── Avoid List
    ├── Korean Skincare Products
    ├── Makeup Shade Matching
    ├── Morning/Night Routine
    └── Weekly Treatment Schedule
    ↓
Save Report + Create ScanMilestone
    ↓
Notify User
```

### PAGE 4: PRODUCT RECOMMENDATION ENGINE

```
AI Analysis
    ↓
Recommendation Engine
    ├── Filter by Skin Concerns
    ├── Filter by Skin Type
    ├── Filter by User Tier (Normal/Medium/VIP)
    ├── Match Undertone (for makeup)
    └── Match Skin Tone (for makeup)
    ↓
Product Categories:
    ├── Korean Skincare (SAS Global brands)
    ├── Makeup (MARS, Maybelline, MAC, etc.)
    ├── Ayurvedic (natural/herbal)
    └── Pharmacy (OTC clinical)
    ↓
Product Display:
    ├── SKU tagging [PRODUCT:SKU:Name]
    ├── Affiliate Links
    ├── Price filtering by tier
    └── Review integration
    ↓
Cart → Checkout → Order Tracking
```

### PAGE 5: PROGRESS TRACKING SYSTEM

```
Day 0: Initial Scan
    ↓
Create ScanMilestone record
    ↓
Daily Routine Log
    ├── AM Routine (cleanser, toner, serum, moisturizer, SPF)
    ├── PM Routine (cleanser, treatment, moisturizer)
    ├── Water intake tracker
    ├── SPF reapplication
    └── Daily skin rating (1-5)
    ↓
Weekly Check-in (every Sunday)
    ├── Overall skin rating
    ├── Hydration rating
    ├── Acne rating
    ├── Brightness rating
    ├── New concerns
    └── Products used
    ↓
Day 14: First Progress Scan
    ↓
AI Comparison (Day 0 vs Day 14)
    ├── Harmony delta
    ├── Hydration delta
    ├── Acne delta
    └── AI verdict (improved/unchanged/declined)
    ↓
Day 30: Monthly Report
    ↓
Day 60: Optimization
    ↓
Day 90: Transformation Report
    ├── Total improvement %
    ├── Before/After photos
    └── Personalized next steps
```

### PAGE 6: MEMBERSHIP & REWARDS SYSTEM

```
Visitor
    ↓
Free AI Face Scan
    ↓
Free Report
    ↓
Signup (with referral code support)
    ↓
Normal Tier (Free)
    ├── Products up to ₹999
    ├── Basic AI consultations
    ├── 1× points on purchases
    └── Log & Earn habits
    ↓
Earn Loyalty Points:
    ├── Daily routine log: +10 pts (AM) +10 pts (PM)
    ├── Weekly check-in: +25 pts
    ├── Milestone scans: +50/+100/+150/+300 pts
    ├── Referral: +100 pts per friend
    └── Purchases: +1 pt per ₹100
    ↓
Redeem Points:
    ├── 500 pts → Upgrade to PLUS (Medium tier)
    └── 1500 pts → Upgrade to VIP
    ↓
OR Purchase Membership:
    ├── PLUS: ₹999/year (products up to ₹2499, 2× points)
    └── VIP: ₹2499/year (unlimited, 3× points, 1:1 Doctor)
    ↓
Tier Benefits:
    ├── Product access by price ceiling
    ├── Points multiplier
    ├── Priority AI responses
    └── VIP: Live doctor consultation
```

### PAGE 7: NOTIFICATION SYSTEM

```
System Events Trigger Notifications:
    ├── scan_reminder (Day 14/30/60/90 due)
    ├── progress_check (weekly check-in reminder)
    ├── tier_upgrade (membership upgraded)
    ├── tier_expiry (subscription expiring soon)
    ├── order_update (order status change)
    ├── points_earned (loyalty points awarded)
    ├── routine_reminder (AM/PM routine pending)
    ├── weekly_checkin (Sunday reminder)
    ├── achievement (milestone completed)
    └── system (general announcements)
    ↓
Notification Model:
    ├── Title
    ├── Message
    ├── Icon (emoji)
    ├── Action URL + Label
    ├── Read/Unread status
    └── Timestamp
    ↓
Display:
    ├── Topbar badge (unread count)
    ├── Notifications page (list view)
    └── Auto-mark as read on view
```

### PAGE 8: ADMIN & EMPLOYEE WORKFLOW

```
Admin Login
    ↓
Dashboard
    ├── User Management
    │   ├── View all users
    │   ├── Tier override (admin bypass payment)
    │   └── Audit logs (tier changes)
    │
    ├── Product Management
    │   ├── CRUD operations
    │   ├── Bulk CSV import
    │   ├── CSV export
    │   └── Product reviews moderation
    │
    ├── Order Management
    │   ├── View all orders
    │   ├── Update order status
    │   ├── Tracking ID generation
    │   └── User requirements (custom requests)
    │
    ├── AI Management
    │   ├── Diagnostic session logs
    │   ├── Marketing analytics
    │   ├── Referral tracking
    │   └── Quiz performance
    │
    ├── Content Management
    │   ├── Blog posts (create, publish, archive)
    │   ├── Coupons (create, expire, track usage)
    │   └── Notifications (broadcast)
    │
    └── Analytics & Reports
        ├── User engagement (scans, routines, check-ins)
        ├── Revenue by tier
        ├── Product performance
        └── Marketing conversion funnel
```

---

## 📁 Application Structure

```
lumina1/
├── apps/
│   ├── accounts/          # Auth, signup, login, password reset
│   ├── blog/              # Blog posts, categories, tags
│   ├── chat/              # AI chat (3 modes: Doctor/Makeup/K-Beauty)
│   ├── core/              # Home, landing pages, context processors
│   ├── coupons/           # Discount codes, validation, usage tracking
│   ├── dashboard/         # User scan history dashboard
│   ├── diagnostic/        # Smart quiz, Log & Earn, marketing portal
│   ├── employee/          # Staff portal, product CRUD, bulk import
│   ├── hair/              # Hair diagnosis wizard (6 steps)
│   ├── memberships/       # Tiers, upgrade, points redemption, VIP doctor
│   ├── notifications/     # User notification system
│   ├── orders/            # Cart, checkout, order tracking, requirements
│   ├── products/          # Product catalog (Korean/Makeup/Ayurvedic/Pharmacy)
│   ├── progress/          # Daily routine log, weekly check-in, milestones
│   ├── results/           # Scan results, AI analysis, progress comparison
│   ├── reviews/           # Product reviews with verification
│   ├── scanner/           # Face scan upload, AI analysis pipeline
│   ├── skin/              # 12-step skin consultation wizard
│   └── treatments/        # Treatment plans (placeholder)
│
├── templates/             # Django templates (Bootstrap 5)
├── static/                # CSS, JS, images
├── media/                 # Uploaded user content (scans, blog images)
├── lumina/                # Django project settings
└── db.sqlite3             # SQLite database (dev)
```

---

## 🗄️ Key Database Models

### Core Models

**User** (Django built-in)
- username, email, password
- first_name, last_name

**UserProfile** (apps.memberships)
- tier: normal/medium/vip
- loyalty_points
- referral_code
- subscription_expires_at
- staff_role: none/marketing/admin

**ScanResult** (apps.scanner)
- scan_image, skin_tone, undertone, face_shape, skin_type
- harmony_score, hydration_score, pigmentation_score, acne_score, aging_score
- hf_acne_severity, hf_skin_type, hf_undertone
- detected_concerns (M2M with SkinConcern)

**SmartDiagSession** (apps.diagnostic)
- answers (JSONField — all quiz responses)
- analysis (JSONField — computed AI analysis)
- severity, top_concern_cat

**SkinSession** (apps.skin)
- 100+ fields covering 12-step consultation
- skin_type_result, acne_severity, recommended_routine

### Progress Tracking Models

**DailyRoutineLog** (apps.progress)
- log_date, am_done, pm_done
- water_glasses, spf_applied, skin_rating (1-5)

**WeeklyCheckin** (apps.progress)
- week_number, overall_rating, hydration_rating, acne_rating, brightness_rating
- new_concerns, products_used

**ScanMilestone** (apps.progress)
- scan_day0, scan_day14, scan_day30, scan_day60, scan_day90
- score_day0, score_day14, score_day30, score_day60, score_day90
- Auto-links scans via signals

### E-commerce Models

**Product** (apps.products)
- name, brand, category, product_range, price, SKU
- suitable_for_skin_types, targets (concern slugs)
- shades_available, undertone_match, skin_tone_match

**Order** (apps.orders)
- order_id, tracking_id, status
- items (OrderItem), total, delivery_charge, discount

**ProductReview** (apps.reviews)
- rating (1-5), title, body
- skin_type, concern, used_for_weeks
- scan_verified, purchase_verified

**Coupon** (apps.coupons)
- code, coupon_type (percent/fixed/free_ship), discount_value
- valid_from, valid_until, max_uses, tier_required

### Content Models

**BlogPost** (apps.blog)
- title, slug, content, cover_image
- category, tags, status (draft/published/archived)
- reading_time, view_count

**Notification** (apps.notifications)
- notif_type, title, message, icon
- action_url, action_label, is_read

---

## 🔑 Key Features Implemented

✅ **AI Face Scanner**
- HuggingFace + xAI integration
- 6-score system (harmony, hydration, pigmentation, acne, aging, elasticity)
- Face shape detection via MediaPipe + xAI Grok

✅ **Smart Diagnostic Quiz**
- 11 sections, ~40 questions, conditional logic
- AI analysis with ingredient recommendations

✅ **12-Step Skin Consultation**
- Detailed 100+ field questionnaire
- Computed skin type + acne severity

✅ **AI Chat Consultants (3 modes)**
- Dr. Lumina (dermatologist)
- Lumina Glam (makeup artist)
- Lumina K (K-Beauty specialist)
- Powered by Groq llama-3.3-70b
- Scan context injection for personalized advice

✅ **Progress Tracking System**
- Daily AM/PM routine log
- Weekly check-in questionnaire
- 0/14/30/60/90-day milestone tracker
- Auto-comparison with progress charts

✅ **3-Tier Membership System**
- Normal (Free), PLUS (₹999/year), VIP (₹2499/year)
- Price ceiling enforcement
- Points multiplier (1×/2×/3×)
- VIP 1:1 doctor chat

✅ **Loyalty Points & Rewards**
- Log & Earn habits (+10 pts per session)
- Weekly check-in (+25 pts)
- Milestone bonuses (+50/+100/+150/+300 pts)
- Referral bonuses (+100 pts)
- Redeem for tier upgrades

✅ **E-commerce**
- 4 product ranges (Korean/Makeup/Ayurvedic/Pharmacy)
- Cart, checkout, order tracking
- User requirements (custom product requests)
- Review system with verification badges

✅ **Notification System**
- 10 notification types
- Unread badge in topbar
- Auto-mark read on view

✅ **Blog System**
- Categories, tags, featured posts
- Markdown content support
- View tracking, reading time

✅ **Coupon System**
- Percentage, fixed, free shipping
- Tier restrictions, usage limits
- Auto-validation at checkout

✅ **Admin/Employee Portal**
- User management with tier override
- Product CRUD + bulk CSV import/export
- Order management
- Diagnostic analytics
- Marketing conversion tracking

---

## 🚀 Next Steps (Not Yet Implemented)

1. **Payment Gateway Integration**
   - Razorpay/Stripe for tier upgrades
   - COD already supported for products

2. **Email Automation**
   - Welcome email
   - Scan reminder emails (Day 14/30/60/90)
   - Weekly check-in reminders
   - Order confirmation emails

3. **Push Notifications**
   - Browser push for scan reminders
   - Mobile app (future)

4. **Doctor Consultation Booking**
   - Live video consultation (VIP feature)
   - Booking calendar integration

5. **Community Forum**
   - User discussions
   - Before/after photo sharing

6. **Advanced Analytics**
   - User cohort analysis
   - A/B testing for quiz questions
   - Product recommendation optimization

---

## 🎨 UI/UX Design System

**Layout:**
- Vertical sidebar navigation (desktop)
- Bottom bar navigation (mobile)
- Sticky topbar with notifications

**Color Palette:**
- Primary: #6c63ff (purple)
- Success: #22c55e (green)
- Gold: #c9a96e (VIP accent)
- Teal: #0d9488 (tier accent)
- Sidebar: #0a0a0f (dark charcoal)

**Typography:**
- Sans: Inter (UI elements)
- Serif: Cormorant Garamond (brand, headings)

**Components:**
- Cards: border-radius 14-16px
- Buttons: border-radius 12-20px
- Badges: border-radius 20px
- Transitions: 0.12-0.25s ease

---

## 📈 Analytics & Metrics Tracked

**User Engagement:**
- Total scans
- Routine completion rate (AM/PM %)
- Weekly check-in participation
- Streak days
- Points earned

**Conversion Funnel:**
- Landing → Signup
- Signup → First Scan
- Scan → Quiz Complete
- Quiz → Product View
- Product View → Purchase
- Free → Paid tier

**Product Performance:**
- Views, clicks, purchases by SKU
- Review count & average rating
- Recommendation acceptance rate

**Marketing:**
- Referral conversion rate
- Diagnostic quiz completion rate
- Tier distribution (Normal/Medium/VIP)
- Coupon usage rate

---

## 🔒 Security Features

✅ File upload validation (size, MIME, magic bytes)
✅ CSRF protection
✅ SQL injection prevention (ORM)
✅ Session security (HttpOnly cookies, 2-hour sliding window)
✅ Rate limiting middleware
✅ Security headers (CSP, X-Frame-Options, etc.)
✅ Password validation (Django validators)
✅ Admin role-based access control
✅ Order/Scan ownership verification (prevent IDOR)

---

## 📝 Environment Variables Required

```bash
SECRET_KEY=<django-secret>
DEBUG=False
ALLOWED_HOSTS=lumina.app,www.lumina.app
DATABASE_URL=<postgres-url>  # optional, uses SQLite by default

# AI APIs
GEMINI_API_KEY=<google-gemini-key>
HF_API_KEY=<huggingface-key>
GROQ_API_KEY=<groq-key>
GROK_API_KEY=<xai-grok-key>
OPENAI_API_KEY=<openai-key>  # optional

# Email
EMAIL_HOST_USER=<gmail-address>
EMAIL_HOST_PASSWORD=<gmail-app-password>
DEFAULT_FROM_EMAIL=Lumina <noreply@lumina.app>
```

---

## 🎯 Deployment Checklist

- [ ] Set `DEBUG=False`
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Set strong `SECRET_KEY`
- [ ] Migrate to PostgreSQL
- [ ] Configure static files (WhiteNoise or CDN)
- [ ] Configure media storage (S3 or similar)
- [ ] Set up email service (SendGrid, AWS SES)
- [ ] Enable HTTPS (SSL certificate)
- [ ] Configure domain DNS
- [ ] Set up monitoring (Sentry, New Relic)
- [ ] Schedule cron jobs (scan reminders, tier expiry checks)
- [ ] Backup strategy for database + media
- [ ] CDN for static assets

---

**Built with ❤️ by SAS Global**  
Version: 1.0.0 | Last Updated: Jan 2025
