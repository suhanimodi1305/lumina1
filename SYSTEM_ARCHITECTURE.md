# Lumina AI — Complete System Architecture Documentation

**Version:** 2.0  
**Last Updated:** July 12, 2026  
**Status:** Production-Ready ✅

---

## 📋 Table of Contents

1. [System Overview](#system-overview)
2. [Architecture Components](#architecture-components)
3. [Application Modules](#application-modules)
4. [Database Schema](#database-schema)
5. [API Integration](#api-integration)
6. [Authentication & Authorization](#authentication--authorization)
7. [Frontend Architecture](#frontend-architecture)
8. [Deployment Guide](#deployment-guide)
9. [Maintenance & Monitoring](#maintenance--monitoring)
10. [Future Roadmap](#future-roadmap)

---

## 🎯 System Overview

### Purpose
Lumina AI is an AI-powered beauty and skincare consultation platform that combines:
- **AI Skin Analysis** — Multi-step diagnostic wizard with conditional logic
- **AI Consultants** — 3 specialized chat modes (Doctor, Makeup, K-Beauty)
- **E-commerce Platform** — Multi-category product marketplace
- **Progress Tracking** — Skincare journey analytics & habit logging
- **Gamification** — Points, streaks, tiered membership system

### Tech Stack
- **Backend:** Django 4.2 (Python 3.12)
- **Database:** PostgreSQL (production) / SQLite (dev)
- **Frontend:** Bootstrap 5.3 + Vanilla JavaScript
- **AI:** OpenAI GPT-4, Claude (Bedrock), Gemini
- **Hosting:** AWS (EC2 + RDS + S3)
- **CDN:** CloudFront for static assets

### Key Statistics
- **40+ question** adaptive diagnostic engine
- **11 conditional sections** (smart skip logic)
- **3 AI consultant modes** with conversation memory
- **4 product categories** (Korean, Ayurvedic, Makeup, Pharmacy)
- **3-tier membership** system (Free, Plus, VIP)
- **8 habit categories** for gamified tracking

---

## 🏗️ Architecture Components

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                            │
│  Bootstrap 5 UI + Vanilla JS + HTMX (for real-time updates)    │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    APPLICATION LAYER (Django)                   │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────────┐  │
│  │  Core    │  Skin    │   Chat   │ Products │  Memberships │  │
│  │  Views   │ Analysis │   AI     │  E-comm  │   Tiers      │  │
│  └──────────┴──────────┴──────────┴──────────┴──────────────┘  │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────────┐  │
│  │Progress  │Diagnostic│   Blog   │ Employee │   Orders     │  │
│  │ Tracker  │  Engine  │  System  │  Portal  │   Coupons    │  │
│  └──────────┴──────────┴──────────┴──────────┴──────────────┘  │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                      DATA LAYER (PostgreSQL)                    │
│  Users │ Profiles │ Products │ Orders │ Scans │ Chats │ Points │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                            │
│  OpenAI GPT-4 │ AWS Bedrock (Claude) │ Google Gemini │ S3      │
└─────────────────────────────────────────────────────────────────┘
```

### Request Flow

```
User Request → Middleware (Auth, CORS, Session) 
    → URL Router → View Function 
    → Business Logic → Database Query
    → AI Service (if needed) → Response Rendering
    → Template + Context → HTTP Response
```

---

## 📦 Application Modules

### 1. **Core** (`apps/core/`)
**Purpose:** Landing pages, public-facing content, theme management

**Key Files:**
- `views.py` — Home, dermatology info, K-beauty guide
- `context_processors.py` — Global template variables (tier, notifications)
- `middleware.py` — Referral tracking, session management
- `urls.py` — Public routes

**Routes:**
- `/` — Landing page
- `/dermatology/` — Educational content
- `/kbeauty/` — K-beauty guide

---

### 2. **Skin** (`apps/skin/`)
**Purpose:** Multi-step AI skin analysis wizard (12 steps)

**Key Files:**
- `views.py` — Step-by-step wizard logic
- `models.py` — `RealScan` model (stores analysis results)

**Flow:**
1. **Start** (`/skin/start/`) — Welcome screen
2. **Steps 1-12** — Conditional questions (skin type, concerns, lifestyle)
3. **Analysis** — AI processing with OpenAI GPT-4
4. **Result** (`/skin/result/<scan_id>/`) — Personalized recommendations

**Key Features:**
- 🎯 Conditional logic (skip irrelevant sections)
- 📸 Photo upload for AI vision analysis
- 🧪 Ingredient recommendation engine
- 🛒 Product matching by concern + skin type

---

### 3. **Diagnostic** (`apps/diagnostic/`)
**Purpose:** Smart diagnostic quiz (40+ questions, 11 sections)

**Key Files:**
- `smart_quiz.py` — Question definitions + conditional logic engine
- `views.py` — Wizard flow, result computation
- `models.py` — `SmartDiagSession`, `HabitLog`, `HabitCategory`

**Sections:**
1. Personal Info (age, gender, climate)
2. Main Skin Concerns (multi-select, max 3)
3. Skin Type (4 questions)
4. **Acne** (conditional — only if 'acne' selected)
5. **Pigmentation** (conditional — dark spots/pigmentation)
6. **Sensitive Skin** (conditional)
7. Lifestyle (water, sleep, stress)
8. Current Routine
9. Makeup (optional section)
10. Product Preferences (budget, vegan, fragrance-free)
11. AI Photo Analysis

**Routes:**
- `/diagnostic/smart/start/` — Begin quiz
- `/diagnostic/smart/question/<step>/` — Each step
- `/diagnostic/smart/save/<step>/` — POST handler
- `/diagnostic/smart/result/<session_id>/` — Analysis result

**Log & Earn System:**
- `/diagnostic/log-earn/` — Habit logging dashboard
- Daily habits: skincare, water, sleep, SPF, meditation, etc.
- Points multiplier: 1× (Free), 2× (Plus), 3× (VIP)
- Streak tracking + leaderboard

---

### 4. **Chat** (`apps/chat/`)
**Purpose:** AI consultant chatbot (3 modes)

**AI Modes:**
1. **🩺 Doctor** — Medical-grade skincare advice (GPT-4)
2. **💄 Makeup AI** — Makeup recommendations (Claude) — **Plus+ only**
3. **🌸 K-Beauty AI** — Korean skincare expert (Gemini) — **Plus+ only**

**Key Files:**
- `ai_service.py` — Multi-provider AI integration (OpenAI, Bedrock, Gemini)
- `views.py` — Chat UI, message handling, room management
- `models.py` — `ChatRoom`, `ChatMessage` (with conversation memory)

**Features:**
- 💬 Real-time streaming (SSE)
- 🧠 Conversation memory (last 10 messages)
- 🔒 Tier-gated access (Doctor = Free, Makeup/K-Beauty = Plus+)
- 📊 Token usage tracking

**Routes:**
- `/chat/` — Chat room list
- `/chat/new/?mode=doctor` — Create new chat
- `/chat/room/<room_id>/` — Chat interface

---

### 5. **Products** (`apps/products/`)
**Purpose:** E-commerce product catalog

**Product Categories:**
- **Korean** (🇰🇷) — K-beauty skincare
- **Makeup** (💄) — Cosmetics & makeup
- **Ayurvedic** (🌿) — Natural/herbal products
- **Pharmacy** (💊) — Derma-grade/clinical

**Key Files:**
- `models.py` — `Product` (name, price, category, ingredients, image)
- `views.py` — Product list (filterable), detail pages

**Features:**
- 🔍 Filter by category, concern, skin type
- 💰 Price range filtering
- ⭐ Review & rating system integration
- 🏷️ Coupon system integration

**Routes:**
- `/products/` — Product list
- `/products/<pk>/` — Product detail

---

### 6. **Orders** (`apps/orders/`)
**Purpose:** E-commerce checkout & order management

**Key Files:**
- `models.py` — `Order`, `OrderItem`, `Requirement` (custom orders)
- `views.py` — Checkout flow, order tracking

**Features:**
- 🛒 Session-based cart
- 💳 Checkout flow (address, payment)
- 📦 Order tracking (pending → shipped → delivered)
- 📋 Custom requirement requests (for unavailable products)

**Routes:**
- `/orders/checkout/` — Cart & checkout
- `/orders/my-orders/` — Order history
- `/orders/tracking/<order_id>/` — Track order

---

### 7. **Memberships** (`apps/memberships/`)
**Purpose:** 3-tier membership system

**Tiers:**
1. **🟢 Free** — Basic access (AI Doctor only)
2. **💜 Plus** — ₹499/mo — Makeup AI + K-Beauty AI + 2× points
3. **👑 VIP** — ₹999/mo — All features + Doctor Live Chat + 3× points

**Key Files:**
- `models.py` — `UserProfile` (tier, points, referral code)
- `views.py` — Upgrade flow, Doctor VIP chat

**Routes:**
- `/membership/upgrade/` — Tier comparison & upgrade
- `/membership/doctor/` — VIP Doctor chat (1-on-1)

---

### 8. **Progress** (`apps/progress/`)
**Purpose:** Skincare journey tracking & analytics

**Key Files:**
- `models.py` — `DailyLog`, `WeeklyCheckin`, `Milestone`
- `views.py` — Dashboard, log entry, analytics

**Features:**
- 📅 Daily skin logs (condition, products used, mood)
- 📊 Weekly check-ins (progress assessment)
- 🏆 Milestone tracker (e.g., "30 days of SPF")
- 📈 Analytics dashboard (charts, trends)

**Routes:**
- `/progress/` — Progress home
- `/progress/daily-log/` — Daily entry form
- `/progress/weekly-checkin/` — Weekly assessment
- `/progress/analytics/` — Charts & insights

---

### 9. **Blog** (`apps/blog/`)
**Purpose:** SEO-optimized content marketing

**Key Files:**
- `models.py` — `BlogPost` (title, slug, content, author, tags)
- `views.py` — Blog list, detail

**Routes:**
- `/blog/` — Blog list
- `/blog/<slug>/` — Blog detail

---

### 10. **Employee** (`apps/employee/`)
**Purpose:** Admin/staff portal

**Key Files:**
- `views.py` — Order management, product CRUD, bulk import
- `models.py` — `EmployeeProfile` (role, permissions)

**Features:**
- 📦 Order fulfillment dashboard
- 🏷️ Product management (CRUD)
- 📥 Bulk product import (CSV)
- 📊 Sales analytics
- 👥 Team management

**Routes:**
- `/employee/portal/` — Dashboard
- `/employee/orders/` — Order list
- `/employee/products/` — Product list
- `/employee/bulk-import/` — CSV import

---

### 11. **Accounts** (`apps/accounts/`)
**Purpose:** User authentication & profile

**Key Files:**
- `views.py` — Login, signup, password reset
- `forms.py` — Custom user forms

**Routes:**
- `/accounts/login/` — Login
- `/accounts/signup/` — Registration
- `/accounts/logout/` — Logout
- `/me/` — User home (dashboard)

---

### 12. **Notifications** (`apps/notifications/`)
**Purpose:** In-app notification system

**Key Files:**
- `models.py` — `Notification` (type, message, read status)
- `views.py` — Notification list

**Routes:**
- `/notifications/` — Notification center

---

### 13. **Coupons** (`apps/coupons/`)
**Purpose:** Discount coupon system

**Key Files:**
- `models.py` — `Coupon` (code, discount, expiry)
- `views.py` — Coupon redemption

**Routes:**
- `/coupons/my-coupons/` — User's coupons

---

### 14. **Reviews** (`apps/reviews/`)
**Purpose:** Product review system

**Key Files:**
- `models.py` — `Review` (product, rating, comment)
- `views.py` — Review submission

**Routes:**
- `/reviews/submit/<product_id>/` — Submit review

---

### 15. **Results** (`apps/results/`)
**Purpose:** Skin scan result display & comparison

**Key Files:**
- `models.py` — Links to `RealScan`
- `views.py` — Result detail, progress comparison

**Routes:**
- `/results/<scan_id>/` — Scan result
- `/results/progress/` — Compare scans over time

---

### 16. **Hair** (`apps/hair/`)
**Purpose:** Hair diagnostic quiz (6 steps)

**Key Files:**
- `views.py` — Hair wizard flow
- `models.py` — `HairScan`

**Routes:**
- `/hair/start/` — Begin hair quiz
- `/hair/step-<n>/` — Quiz steps
- `/hair/result/` — Hair analysis result

---

## 🗄️ Database Schema

### Core Models

#### **User** (Django built-in)
```python
- id (PK)
- username (unique)
- email (unique)
- password (hashed)
- first_name
- last_name
- is_staff
- is_active
- date_joined
```

#### **UserProfile** (`apps/memberships/models.py`)
```python
- user (OneToOne → User)
- phone
- tier (normal, medium, vip)
- loyalty_points (default 0)
- referral_code (unique)
- referred_by (FK → User)
- staff_role (marketing, admin, sales, etc.)
- address fields (street, city, state, zip)
- created_at, updated_at
```

#### **RealScan** (`apps/skin/models.py`)
```python
- id (PK)
- user (FK → User)
- skin_type (oily, dry, combo, normal)
- primary_concern
- secondary_concern
- age_group
- gender
- climate
- lifestyle_score (0-100)
- ai_analysis (JSONField) — full AI response
- recommendations (JSONField) — products, ingredients
- photo (ImageField, nullable)
- created_at
```

#### **SmartDiagSession** (`apps/diagnostic/models.py`)
```python
- id (UUID PK)
- user (FK → User, nullable)
- session_key
- answers (JSONField) — all 40+ answers
- analysis (JSONField) — computed result
- severity (mild, moderate, severe)
- top_concern_cat
- primary_goal
- completed (bool)
- created_at
```

#### **ChatRoom** (`apps/chat/models.py`)
```python
- id (PK)
- user (FK → User)
- mode (doctor, makeup, kbeauty)
- title
- created_at, updated_at
```

#### **ChatMessage** (`apps/chat/models.py`)
```python
- id (PK)
- room (FK → ChatRoom)
- sender (user, ai)
- content (text)
- tokens_used (int)
- created_at
```

#### **Product** (`apps/products/models.py`)
```python
- id (PK)
- name
- slug (unique)
- description
- ingredients (text)
- price (Decimal)
- discounted_price (Decimal, nullable)
- product_range (korean, makeup, ayurvedic, pharmacy)
- skin_types (ArrayField — oily, dry, combo, normal)
- concerns (ArrayField — acne, pigmentation, aging, etc.)
- image (ImageField)
- stock_quantity (int)
- is_active (bool)
- created_at, updated_at
```

#### **Order** (`apps/orders/models.py`)
```python
- id (PK)
- user (FK → User)
- order_number (unique, e.g. LUM-20260712-1234)
- status (pending, paid, shipped, delivered, cancelled)
- subtotal, discount, total (Decimals)
- shipping_address (JSONField)
- payment_method
- tracking_number
- notes (text)
- created_at, updated_at
```

#### **OrderItem** (`apps/orders/models.py`)
```python
- id (PK)
- order (FK → Order)
- product (FK → Product)
- quantity (int)
- price_at_purchase (Decimal)
```

#### **HabitCategory** (`apps/diagnostic/models.py`)
```python
- slug (PK, e.g. skincare_morning)
- title (e.g. "Morning Skincare")
- icon (emoji)
- description
- points (int, default 5)
```

#### **HabitLog** (`apps/diagnostic/models.py`)
```python
- id (PK)
- user (FK → User)
- habit (FK → HabitCategory)
- points_earned (int) — includes tier multiplier
- logged_at (DateTime)
```

#### **Notification** (`apps/notifications/models.py`)
```python
- id (PK)
- user (FK → User)
- type (order, scan, points, system)
- message (text)
- link (URL, nullable)
- is_read (bool, default False)
- created_at
```

#### **Coupon** (`apps/coupons/models.py`)
```python
- code (PK, e.g. SUMMER25)
- discount_percent (Decimal)
- valid_from, valid_to (DateFields)
- usage_limit (int)
- times_used (int, default 0)
- is_active (bool)
```

#### **BlogPost** (`apps/blog/models.py`)
```python
- id (PK)
- title
- slug (unique)
- content (rich text)
- author (FK → User)
- tags (ArrayField)
- featured_image (ImageField)
- is_published (bool)
- published_at
- created_at, updated_at
```

---

## 🔌 API Integration

### AI Service Configuration

**File:** `apps/chat/ai_service.py`

```python
AI_PROVIDERS = {
    'doctor':  {'provider': 'openai',  'model': 'gpt-4-turbo'},
    'makeup':  {'provider': 'bedrock', 'model': 'anthropic.claude-3-sonnet'},
    'kbeauty': {'provider': 'gemini',  'model': 'gemini-1.5-flash'},
}
```

### Environment Variables (`.env`)

```bash
# Django
SECRET_KEY=...
DEBUG=False
ALLOWED_HOSTS=lumina.ai,www.lumina.ai

# Database
DATABASE_URL=postgresql://user:pass@host:5432/lumina_db

# AWS
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_STORAGE_BUCKET_NAME=lumina-media
AWS_S3_REGION_NAME=ap-south-1
AWS_BEDROCK_REGION=us-east-1

# OpenAI
OPENAI_API_KEY=sk-...

# Google AI
GOOGLE_API_KEY=AIza...

# Email (Production)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=support@lumina.ai
EMAIL_HOST_PASSWORD=...

# Stripe (Payment)
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
```

---

## 🔐 Authentication & Authorization

### User Tiers

| Tier | Price | Features | Points Multiplier |
|------|-------|----------|-------------------|
| **Free** | ₹0 | AI Doctor, Basic scans | 1× |
| **Plus** | ₹499/mo | + Makeup AI, K-Beauty AI | 2× |
| **VIP** | ₹999/mo | + VIP Doctor chat, Premium products | 3× |

### Permission Checks

```python
# View decorator example
from apps.memberships.decorators import tier_required

@tier_required('medium')  # Requires Plus or VIP
def makeup_chat(request):
    ...
```

### Staff Roles (`UserProfile.staff_role`)
- `admin` — Full system access
- `marketing` — Analytics, referral tracking
- `sales` — Order management
- `support` — Customer queries
- `content` — Blog management

---

## 🎨 Frontend Architecture

### UI Framework
- **Bootstrap 5.3** — Responsive grid, components
- **Custom CSS** — `static/css/style.css` (600+ lines)
- **Icons** — Bootstrap Icons (self-hosted, no CDN)

### Layout System

```
base.html (master template)
├── Sidebar (vertical navigation)
├── Topbar (notifications, theme toggle, search)
├── Main Content Area
└── Mobile Bottom Bar (< 991px)
```

### Theme System

**Light/Dark Mode:**
- Stored in `localStorage` as `lux_theme`
- Applied before first paint (prevents flash)
- Toggleable via topbar button

### JavaScript Architecture

**Main Files:**
- `static/js/main.js` — Core functionality (theme, sidebar, cart)
- `static/js/chat.js` — Real-time chat with SSE
- `static/js/wizard.js` — Step validation & progress

**Libraries:**
- AOS (Animate On Scroll)
- Chart.js (for analytics)
- Bootstrap 5 (no jQuery)

---

## 🚀 Deployment Guide

### Prerequisites
1. Ubuntu 20.04+ server (AWS EC2 recommended)
2. PostgreSQL 14+
3. Python 3.12+
4. Nginx
5. Gunicorn
6. Supervisor (for process management)

### Step-by-Step Deployment

#### 1. Server Setup
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install python3.12 python3.12-venv python3-pip postgresql nginx supervisor git -y

# Create app user
sudo adduser lumina
sudo usermod -aG sudo lumina
```

#### 2. Clone & Setup Project
```bash
# Switch to app user
su - lumina

# Clone repository
git clone https://github.com/yourusername/lumina-ai.git
cd lumina-ai

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

#### 3. Configure Environment
```bash
# Create .env file
cp .env.example .env
nano .env

# Set production values
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
DATABASE_URL=postgresql://user:pass@localhost:5432/lumina_prod
```

#### 4. Database Setup
```bash
# Create PostgreSQL database
sudo -u postgres psql
CREATE DATABASE lumina_prod;
CREATE USER lumina_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE lumina_prod TO lumina_user;
\q

# Run migrations
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic --noinput
```

#### 5. Configure Gunicorn

**File:** `/home/lumina/lumina-ai/gunicorn_config.py`
```python
bind = '127.0.0.1:8000'
workers = 4  # (2 × CPU cores) + 1
worker_class = 'sync'
timeout = 120
accesslog = '/var/log/gunicorn/access.log'
errorlog = '/var/log/gunicorn/error.log'
loglevel = 'info'
```

#### 6. Supervisor Configuration

**File:** `/etc/supervisor/conf.d/lumina.conf`
```ini
[program:lumina]
command=/home/lumina/lumina-ai/venv/bin/gunicorn config.wsgi:application -c /home/lumina/lumina-ai/gunicorn_config.py
directory=/home/lumina/lumina-ai
user=lumina
autostart=true
autorestart=true
stderr_logfile=/var/log/supervisor/lumina.err.log
stdout_logfile=/var/log/supervisor/lumina.out.log
```

```bash
# Reload supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start lumina
```

#### 7. Nginx Configuration

**File:** `/etc/nginx/sites-available/lumina`
```nginx
server {
    listen 80;
    server_name lumina.ai www.lumina.ai;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /home/lumina/lumina-ai/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location /media/ {
        alias /home/lumina/lumina-ai/media/;
        expires 7d;
    }

    client_max_body_size 20M;
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/lumina /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

#### 8. SSL Certificate (Let's Encrypt)
```bash
sudo apt install certbot python3-certbot-nginx -y
sudo certbot --nginx -d lumina.ai -d www.lumina.ai
```

---

## 🔧 Maintenance & Monitoring

### Health Checks

```bash
# Check Gunicorn status
sudo supervisorctl status lumina

# Check Nginx status
sudo systemctl status nginx

# Check logs
tail -f /var/log/supervisor/lumina.err.log
tail -f /var/log/nginx/error.log
```

### Database Backups

```bash
# Automated daily backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
pg_dump -U lumina_user lumina_prod > /backups/lumina_$DATE.sql
find /backups -name "lumina_*.sql" -mtime +7 -delete
```

Add to crontab:
```bash
0 2 * * * /path/to/backup_script.sh
```

### Performance Monitoring

**Tools:**
- **Sentry** — Error tracking
- **New Relic** — APM (Application Performance Monitoring)
- **AWS CloudWatch** — Server metrics

### Django Management Commands

```bash
# Create superuser
python manage.py createsuperuser

# Generate sample data (dev only)
python manage.py loaddata fixtures/sample_products.json

# Clear expired sessions
python manage.py clearsessions

# Rebuild search index (if using Elasticsearch)
python manage.py rebuild_index
```

---

## 🛣️ Future Roadmap

### Q3 2026
- [ ] Mobile app (React Native)
- [ ] Voice consultation (Whisper API)
- [ ] AR virtual try-on (makeup)
- [ ] Subscription billing automation

### Q4 2026
- [ ] Multi-language support (Hindi, Tamil, Bengali)
- [ ] WhatsApp integration (order tracking)
- [ ] Influencer affiliate program
- [ ] Video consultations

### 2027
- [ ] Franchise portal (multi-clinic support)
- [ ] Telemedicine integration
- [ ] Personalized product bundles
- [ ] AI skin aging predictor

---

## 📞 Support & Contact

**Developer:** SAS Global  
**Email:** support@sasglobal.biz  
**Website:** https://sasglobal.biz  
**Documentation:** https://docs.lumina.ai  

---

## 📄 License

Proprietary — All rights reserved © 2026 SAS Global

---

**Last Updated:** July 12, 2026  
**Version:** 2.0.0  
**Status:** ✅ Production-Ready
