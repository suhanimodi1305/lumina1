# Lumina AI Beauty Platform — Laravel 12 Edition

AI-powered beauty advisor: skin analysis, makeup matching, K-Beauty routines, doctor consultations.

---

## Stack

| Layer         | Technology                        |
|---------------|-----------------------------------|
| Web App       | Laravel 12 / PHP 8.3              |
| Auth          | Laravel Breeze + Spatie Permission|
| Admin         | Filament 3                        |
| Queue         | Laravel Horizon / Redis           |
| AI Service    | FastAPI (Python) — unchanged code |
| Database      | MySQL 8.0                         |
| Cache         | Redis                             |

---

## Local Setup

### Prerequisites
- PHP 8.3+
- Composer
- MySQL 8.0
- Redis
- Node.js 20+ (for assets)
- Python 3.11+ with existing venv (`.venv-1`)

### 1. Install dependencies
```bash
cd lumina-laravel
composer install
npm install && npm run build
```

### 2. Environment
```bash
cp .env.example .env
php artisan key:generate
```

Edit `.env`:
```
DB_DATABASE=lumina_beauty
DB_USERNAME=root
DB_PASSWORD=

AI_SERVICE_URL=http://localhost:8001
AI_SERVICE_TOKEN=your-secret-token-here
```

### 3. Database
```bash
php artisan migrate
php artisan db:seed
```

### 4. Storage link
```bash
php artisan storage:link
```

### 5. Start Python AI Service
```bash
cd python-ai-service
# Windows:
start.bat

# Linux/Mac:
source ../.venv-1/bin/activate
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

### 6. Start Laravel
```bash
php artisan serve
```

### 7. Start Queue Worker (optional, for emails/sync)
```bash
php artisan horizon
```

---

## Default Admin
URL: `http://localhost:8000/admin`
Email: `admin@lumina.beauty`
Password: `admin@lumina123`

---

## Key URLs

| URL                  | Description               |
|----------------------|---------------------------|
| `/`                  | Homepage                  |
| `/scan`              | AI Skin Scanner           |
| `/chat`              | AI Chat (Dr. Lumina)      |
| `/products`          | Product Catalog           |
| `/doctor`            | Doctor Consultation       |
| `/membership`        | Membership Plans          |
| `/rewards`           | Log & Earn Rewards        |
| `/me`                | Personal Dashboard        |
| `/admin`             | Filament Admin Panel      |
| `/employee`          | Employee Portal           |
| `/marketing`         | Marketing Dashboard       |

---

## Artisan Commands

```bash
php artisan makeup:sync              # Manual Makeup API sync
php artisan makeup:sync --category=lipstick
php artisan memberships:expire-check # Check expired subscriptions
php artisan scans:cleanup-demo       # Remove old demo scans
```

---

## Architecture

```
User → Laravel 12 → REST API → FastAPI (Python)
                                  ├── Groq API (llama-3.3-70b)
                                  ├── HuggingFace APIs
                                  ├── OpenCV / MediaPipe
                                  └── Gemini AI
                 ↓
              MySQL ← All data stored here
```

The FastAPI service imports the **existing** `apps/chat/ai_service.py` and
`apps/scanner/hf_analyzer.py` directly — **no Python code was rewritten**.
