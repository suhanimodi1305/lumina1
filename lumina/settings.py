"""
Django settings for lumina project.
"""

from pathlib import Path
import dj_database_url
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# No insecure default — the app will fail loudly if SECRET_KEY is not set in .env
SECRET_KEY = config('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
# Defaults to False (safe); set DEBUG=True in .env for local development only.
DEBUG = config('DEBUG', default=False, cast=bool)

configured_hosts = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,.onrender.com')
render_hostname = config('RENDER_EXTERNAL_HOSTNAME', default='').strip()
ALLOWED_HOSTS = [host.strip() for host in configured_hosts.split(',') if host.strip()]
if render_hostname and render_hostname not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(render_hostname)
if '.onrender.com' not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append('.onrender.com')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Lumina apps
    'apps.core',
    'apps.accounts',
    'apps.scanner',
    'apps.results',
    'apps.products',
    'apps.treatments',
    'apps.chat',
    'apps.dashboard',
    'apps.employee',
    'apps.orders',
    'apps.memberships',
    'apps.diagnostic',
    'apps.skin',
    # New system-design apps
    'apps.notifications',
    'apps.progress',
    'apps.reviews',
    'apps.coupons',
    'apps.blog',
    # Admin ERP panel
    'apps.admin_panel',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'apps.memberships.middleware.TierExpiryMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # ── Lumina security ──────────────────────────────────────────────────
    'apps.core.middleware.RateLimitMiddleware',        # brute-force / DoS
    'apps.core.middleware.SecurityHeadersMiddleware',  # CSP + hardening headers
    'apps.core.middleware.SessionExpiryMiddleware',    # server-side session expiry
]

ROOT_URLCONF = 'lumina.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'apps.core.context_processors.user_scan_context',
                'apps.memberships.context_processors.user_tier_context',
                'apps.notifications.context_processors.unread_notifications',
            ],
        },
    },
]

WSGI_APPLICATION = 'lumina.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases

DATABASES = {
    'default': dj_database_url.parse(
        config('DATABASE_URL'),
        conn_max_age=600,
        ssl_require=not DEBUG,
    ) if config('DATABASE_URL', default='').strip() else {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    },
}


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
# In development, use simple storage (no hashing) so Django's built-in
# static file server works correctly alongside WhiteNoise.
# In production (DEBUG=False), WhiteNoise compresses and hashes files.
if DEBUG:
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
else:
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── EMAIL (SMTP via Gmail) ────────────────────────────────────────────────────
EMAIL_BACKEND       = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST          = 'smtp.gmail.com'
EMAIL_PORT          = 587
EMAIL_USE_TLS       = True
EMAIL_HOST_USER     = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL  = config('DEFAULT_FROM_EMAIL', default='Lumina <noreply@lumina.app>')
SERVER_EMAIL        = EMAIL_HOST_USER

# Authentication settings
LOGIN_URL          = '/accounts/login/'
LOGIN_REDIRECT_URL = '/me/'        # After login → personal home
LOGOUT_REDIRECT_URL = '/'

# API Keys
GEMINI_API_KEY = config('GEMINI_API_KEY', default='')
HF_API_KEY = config('HF_API_KEY', default='')
GROQ_API_KEY = config('GROQ_API_KEY', default='')
OPENAI_API_KEY = config('OPENAI_API_KEY', default='')
GROK_API_KEY = config('GROK_API_KEY', default='')   # xAI Grok — for face shape classification

# ── SECURITY SETTINGS ─────────────────────────────────────────────────────────

# Session security
SESSION_COOKIE_HTTPONLY  = True   # JS cannot access session cookie
SESSION_COOKIE_SAMESITE  = 'Lax'  # CSRF protection for cross-site requests
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_COOKIE_AGE = 60 * 60 * 2   # 2 hours — auto-logout after inactivity
SESSION_SAVE_EVERY_REQUEST = True   # Sliding window: reset timer on each request

# CSRF
CSRF_COOKIE_HTTPONLY = False   # Must be False so JS can read it for AJAX
CSRF_COOKIE_SAMESITE = 'Lax'
configured_csrf_origins = config(
    'CSRF_TRUSTED_ORIGINS',
    default='http://localhost:8000,http://127.0.0.1:8000,https://*.onrender.com'
)
CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in configured_csrf_origins.split(',') if origin.strip()]
if render_hostname:
    render_origin = f'https://{render_hostname}'
    if render_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(render_origin)
if 'https://*.onrender.com' not in CSRF_TRUSTED_ORIGINS:
    CSRF_TRUSTED_ORIGINS.append('https://*.onrender.com')

# Proxy SSL header (REQUIRED for PaaS like Render where SSL is terminated at reverse proxy)
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Clickjacking protection (also set by XFrameOptionsMiddleware)
X_FRAME_OPTIONS = 'DENY'

# Content type sniffing protection
SECURE_CONTENT_TYPE_NOSNIFF = True

# XSS filter (legacy browsers)
SECURE_BROWSER_XSS_FILTER = True

# Referrer policy
SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'

# ── PRODUCTION-ONLY HTTPS SETTINGS (enabled when DEBUG=False) ─────────────────
if not DEBUG:
    SECURE_SSL_REDIRECT             = True   # Redirect all HTTP → HTTPS
    SECURE_HSTS_SECONDS             = 31536000  # 1 year HSTS header
    SECURE_HSTS_INCLUDE_SUBDOMAINS  = True
    SECURE_HSTS_PRELOAD             = True
    SESSION_COOKIE_SECURE           = True   # Session cookie only over HTTPS
    CSRF_COOKIE_SECURE              = True   # CSRF cookie only over HTTPS

# ── FILE UPLOAD SECURITY ──────────────────────────────────────────────────────
# Max upload size: 5 MB for scan images, 2 MB for chat photos
DATA_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024   # 5 MB total POST body
FILE_UPLOAD_MAX_MEMORY_SIZE = 5 * 1024 * 1024   # 5 MB per file

# Allowed image MIME types for uploaded scans / chat photos
ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp', 'image/gif']
ALLOWED_IMAGE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.webp', '.gif']

# Max CSV size for bulk import (1 MB)
MAX_CSV_UPLOAD_BYTES = 1 * 1024 * 1024

# ── LOGGING ───────────────────────────────────────────────────────────────────
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'security_file': {
            'class': 'logging.FileHandler',
            'filename': LOG_DIR / 'security.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django.security': {
            'handlers': ['console', 'security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'apps.core.middleware': {
            'handlers': ['console', 'security_file'],
            'level': 'WARNING',
            'propagate': False,
        },
        'apps.accounts': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# ── MEMBERSHIP TIER PRICE BANDS ───────────────────────────────────────────────
NORMAL_PRICE_MAX  = 999     # ₹ — Normal tier ceiling
MEDIUM_PRICE_MAX  = 2499    # ₹ — Medium tier ceiling
# VIP: no ceiling (None)

# ── LOG & EARN POINTS CONFIG ──────────────────────────────────────────────────
REFERRAL_POINTS         = 100   # Points awarded to referrer on first login of referred user
PURCHASE_POINTS_RATE    = 1     # Points per ₹100 spent (floor division)
UPGRADE_POINTS_MEDIUM   = 500   # Points needed to upgrade Normal → Medium
UPGRADE_POINTS_VIP      = 1500  # Points needed to upgrade Medium → VIP
