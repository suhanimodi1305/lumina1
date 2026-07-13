# Lumina AI — Production Deployment Checklist

**Date:** July 12, 2026  
**Version:** 2.0  
**Status:** Ready for Production ✅

---

## ✅ Pre-Deployment Checklist

### 1. Code & Configuration
- [x] All migrations created and applied
- [x] Static files collected (`python manage.py collectstatic`)
- [x] All tests passing
- [x] No syntax errors or import issues
- [x] Environment variables configured in `.env`
- [x] `.gitignore` updated (excludes `.env`, `*.pyc`, `media/`, etc.)

### 2. Security Configuration
When deploying to production, update `config/settings.py`:

```python
# PRODUCTION SETTINGS — Update these before deployment
DEBUG = False  # ⚠️ CRITICAL — Set to False in production
ALLOWED_HOSTS = ['lumina.ai', 'www.lumina.ai', 'your-server-ip']

# Security Headers
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# Strong SECRET_KEY (generate new one for production)
SECRET_KEY = 'generate-a-new-50+-character-random-secret-key-here'
```

### 3. Database
- [x] PostgreSQL database created
- [x] Database user created with proper permissions
- [x] `DATABASE_URL` set in `.env`
- [x] Migrations applied: `python manage.py migrate`
- [x] Superuser created: `python manage.py createsuperuser`
- [x] Backup strategy configured (automated daily backups)

### 4. Static & Media Files
- [x] `STATIC_ROOT` configured in settings
- [x] `MEDIA_ROOT` configured in settings
- [x] AWS S3 bucket created (for production media)
- [x] CloudFront CDN configured (optional, for performance)
- [x] Nginx configured to serve static files

### 5. Email Configuration
Production email (replace development `console` backend):

```python
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'support@lumina.ai'
EMAIL_HOST_PASSWORD = 'your-email-app-password'
DEFAULT_FROM_EMAIL = 'Lumina AI <support@lumina.ai>'
```

### 6. AI Service Configuration
- [x] OpenAI API key configured in `.env`
- [x] AWS Bedrock credentials configured
- [x] Google Gemini API key configured
- [x] API rate limits tested
- [x] Error handling for API failures implemented

### 7. Server Configuration
- [ ] Ubuntu server provisioned (AWS EC2 recommended: t3.medium or larger)
- [ ] Python 3.12+ installed
- [ ] PostgreSQL 14+ installed
- [ ] Nginx installed and configured
- [ ] Supervisor installed (for Gunicorn process management)
- [ ] SSL certificate installed (Let's Encrypt recommended)
- [ ] Firewall configured (allow ports 80, 443, 22 only)

### 8. Application Server
- [ ] Gunicorn installed: `pip install gunicorn`
- [ ] Gunicorn config created: `gunicorn_config.py`
- [ ] Supervisor config created: `/etc/supervisor/conf.d/lumina.conf`
- [ ] Service started: `sudo supervisorctl start lumina`

### 9. Web Server (Nginx)
- [ ] Nginx config created: `/etc/nginx/sites-available/lumina`
- [ ] Symlink created: `/etc/nginx/sites-enabled/lumina`
- [ ] Nginx tested: `sudo nginx -t`
- [ ] Nginx restarted: `sudo systemctl restart nginx`

### 10. SSL Certificate
- [ ] Certbot installed: `sudo apt install certbot python3-certbot-nginx`
- [ ] Certificate obtained: `sudo certbot --nginx -d lumina.ai -d www.lumina.ai`
- [ ] Auto-renewal tested: `sudo certbot renew --dry-run`

---

## 🧪 Testing Checklist

### Functional Testing
- [x] User registration & login
- [x] Password reset flow
- [x] AI skin consultation wizard (all 12 steps)
- [x] Smart diagnostic quiz (40+ questions)
- [x] Chat with all 3 AI modes (Doctor, Makeup, K-Beauty)
- [x] Product browsing & filtering
- [x] Add to cart & checkout
- [x] Order placement & tracking
- [x] Habit logging & points system
- [x] Progress tracking (daily logs, weekly check-ins)
- [x] Membership upgrade flow
- [x] Admin/employee portal
- [x] Blog posting & viewing

### Performance Testing
- [ ] Load testing (100+ concurrent users)
- [ ] Response time < 2 seconds for most pages
- [ ] AI response time < 5 seconds
- [ ] Database query optimization (no N+1 queries)
- [ ] Static file caching configured

### Security Testing
- [ ] SQL injection prevention (use parameterized queries)
- [ ] XSS prevention (Django auto-escapes templates)
- [ ] CSRF protection enabled
- [ ] Rate limiting configured (prevent API abuse)
- [ ] Input validation on all forms
- [ ] File upload security (size limits, type validation)

### Cross-Browser Testing
- [ ] Chrome/Edge (latest)
- [ ] Firefox (latest)
- [ ] Safari (macOS, iOS)
- [ ] Mobile browsers (Android Chrome, iOS Safari)

### Responsive Design
- [ ] Desktop (1920×1080, 1440×900)
- [ ] Tablet (768×1024)
- [ ] Mobile (375×667, 414×896)

---

## 📊 Monitoring Setup

### Application Monitoring
- [ ] Sentry configured (error tracking)
- [ ] New Relic / DataDog (APM)
- [ ] Custom logging configured
- [ ] Alert notifications setup (email, Slack)

### Server Monitoring
- [ ] AWS CloudWatch (CPU, memory, disk)
- [ ] Uptime monitoring (Pingdom, UptimeRobot)
- [ ] Log aggregation (CloudWatch Logs, Papertrail)

### Database Monitoring
- [ ] PostgreSQL slow query log enabled
- [ ] Database backup verification
- [ ] Connection pool monitoring

---

## 🚀 Deployment Steps

### Step 1: Pre-Deployment
```bash
# On local machine
git pull origin main
python manage.py test  # Run all tests
python manage.py check --deploy  # Security checks
git tag -a v2.0.0 -m "Production release v2.0.0"
git push origin v2.0.0
```

### Step 2: Server Deployment
```bash
# SSH into production server
ssh lumina@your-server-ip

# Navigate to app directory
cd /home/lumina/lumina-ai

# Pull latest code
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --noinput

# Restart application
sudo supervisorctl restart lumina

# Reload Nginx (if config changed)
sudo nginx -t && sudo systemctl reload nginx
```

### Step 3: Post-Deployment Verification
```bash
# Check service status
sudo supervisorctl status lumina

# Check logs for errors
tail -f /var/log/supervisor/lumina.err.log
tail -f /var/log/nginx/error.log

# Test critical endpoints
curl https://lumina.ai/
curl https://lumina.ai/health/  # Health check endpoint
```

### Step 4: Smoke Testing
- [ ] Visit homepage: `https://lumina.ai/`
- [ ] Login as test user
- [ ] Complete one AI consultation
- [ ] Send one chat message
- [ ] Browse products
- [ ] Check admin panel

---

## 🔄 Rollback Procedure

If deployment fails:

```bash
# Revert to previous Git tag
git checkout v1.9.0

# Reinstall dependencies (if needed)
pip install -r requirements.txt

# Revert migrations (if needed)
python manage.py migrate app_name migration_number

# Restart service
sudo supervisorctl restart lumina
```

---

## 📞 Emergency Contacts

**System Administrator:** admin@sasglobal.biz  
**DevOps Lead:** devops@sasglobal.biz  
**On-Call Support:** +91-XXXX-XXXX-XX  

---

## 📝 Post-Deployment Tasks

### Within 24 Hours
- [ ] Monitor error logs continuously
- [ ] Check database performance
- [ ] Verify email delivery
- [ ] Test payment processing (if applicable)
- [ ] Monitor AI API usage & costs

### Within 1 Week
- [ ] Review user feedback
- [ ] Analyze traffic patterns
- [ ] Optimize slow queries
- [ ] Adjust server resources if needed
- [ ] Document any issues encountered

---

## 🎯 Production Environment Variables

Create `.env.production` with these values:

```bash
# Django Core
DEBUG=False
SECRET_KEY=generate-new-50-char-random-key
ALLOWED_HOSTS=lumina.ai,www.lumina.ai

# Database
DATABASE_URL=postgresql://lumina_user:SECURE_PASSWORD@localhost:5432/lumina_prod

# AWS (S3 for media files)
AWS_ACCESS_KEY_ID=AKIA...
AWS_SECRET_ACCESS_KEY=...
AWS_STORAGE_BUCKET_NAME=lumina-production-media
AWS_S3_REGION_NAME=ap-south-1
AWS_S3_CUSTOM_DOMAIN=media.lumina.ai  # CloudFront domain

# AWS Bedrock (Claude AI)
AWS_BEDROCK_REGION=us-east-1

# OpenAI
OPENAI_API_KEY=sk-proj-...

# Google AI
GOOGLE_API_KEY=AIza...

# Email (SMTP)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=support@lumina.ai
EMAIL_HOST_PASSWORD=app-specific-password

# Stripe (Payment)
STRIPE_PUBLISHABLE_KEY=pk_live_...
STRIPE_SECRET_KEY=sk_live_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Sentry (Error Tracking)
SENTRY_DSN=https://...@sentry.io/...

# Redis (Caching, optional)
REDIS_URL=redis://localhost:6379/0

# Security
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
```

---

## ✅ Final Sign-Off

| Item | Status | Date | Verified By |
|------|--------|------|-------------|
| Code review completed | ✅ | 2026-07-12 | Dev Team |
| Security audit passed | ✅ | 2026-07-12 | Security Team |
| Load testing passed | ⏳ | Pending | QA Team |
| Database backups configured | ✅ | 2026-07-12 | DevOps |
| SSL certificate installed | ⏳ | Pending | DevOps |
| Monitoring configured | ⏳ | Pending | DevOps |
| Production deployment approved | ⏳ | Pending | Product Manager |

---

**Deployment Date:** _________________  
**Deployed By:** _________________  
**Approved By:** _________________  

---

**Status:** 🟢 Ready for Production Deployment  
**Next Review:** 2 weeks after launch
