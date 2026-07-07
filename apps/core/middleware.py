"""
Lumina Security Middleware
─────────────────────────
1. RateLimitMiddleware      – brute-force / DoS protection (in-memory, per-IP)
2. SecurityHeadersMiddleware – extra hardening headers on every response
3. SessionExpiryMiddleware  – server-side session expiry with clean logout
"""
import time
import logging
from collections import defaultdict
from threading import Lock

from django.conf import settings
from django.contrib.auth import logout as auth_logout
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

# ── Thread-safe in-memory rate-limit store ───────────────────────────────────
_rate_store: dict[str, list[float]] = defaultdict(list)
_rate_lock = Lock()


def _get_client_ip(request) -> str:
    """
    Extract the real client IP.
    Trusts only the last hop when X-Forwarded-For is present to prevent spoofing.
    """
    xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if xff:
        return xff.split(',')[-1].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


# ── Rate limit configuration per path prefix ────────────────────────────────
# (path_prefix, max_requests, window_seconds)
RATE_RULES = [
    ('/accounts/login/',  10, 60),
    ('/accounts/signup/', 5,  60),
    ('/scan/',            20, 60),
    ('/chat/',            60, 60),
    ('/orders/',          30, 60),
]


class RateLimitMiddleware(MiddlewareMixin):
    """
    Simple sliding-window rate limiter.
    Returns HTTP 429 when a client exceeds the configured threshold.
    """

    def process_request(self, request):
        ip   = _get_client_ip(request)
        path = request.path_info
        now  = time.time()

        for prefix, max_req, window in RATE_RULES:
            if not path.startswith(prefix):
                continue

            key = f"{ip}:{prefix}"
            with _rate_lock:
                hits = [t for t in _rate_store[key] if now - t < window]
                if len(hits) >= max_req:
                    logger.warning(
                        "Rate limit exceeded | IP=%s path=%s hits=%d/%d",
                        ip, prefix, len(hits), max_req,
                    )
                    return HttpResponse(
                        "<h1>429 Too Many Requests</h1>"
                        "<p>You are making requests too quickly. Please slow down.</p>",
                        status=429,
                        content_type="text/html",
                    )
                hits.append(now)
                _rate_store[key] = hits
            break

        return None


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Adds security-hardening HTTP response headers to every response."""

    def process_response(self, request, response):
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response['Permissions-Policy'] = (
            'geolocation=(), microphone=(), '
            'payment=(), usb=(), magnetometer=(), gyroscope=()'
            # camera= intentionally omitted so the Face Scan page can call getUserMedia
        )
        response['Content-Security-Policy'] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com https://cdnjs.cloudflare.com; "
            "img-src 'self' data: blob: https:; "
            "media-src 'self' blob:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self';"
        )
        return response


# ── Paths that never trigger session expiry checks ───────────────────────────
_EXPIRY_SKIP_PREFIXES = (
    '/static/', '/media/', '/favicon',
)
_EXPIRY_SKIP_EXACT = {
    '/accounts/session-status/',
    '/accounts/session-ping/',
}


class SessionExpiryMiddleware(MiddlewareMixin):
    """
    Server-side session expiry enforcement.

    How it works:
    ─────────────
    • On every authenticated request it compares now() against the Django
      session's _session_expiry timestamp (set by Django's session framework
      when SESSION_COOKIE_AGE is configured).
    • If the session has expired server-side it logs the user out, clears
      the session, and redirects to login with a clear "session expired"
      message.
    • Skip paths (static, media, status ping) are excluded to avoid noise.
    • Works for regular users, staff/employees, AND the Django admin.
    """

    def process_request(self, request):
        path = request.path_info

        # Skip non-HTML paths
        if any(path.startswith(p) for p in _EXPIRY_SKIP_PREFIXES):
            return None
        if path in _EXPIRY_SKIP_EXACT:
            return None

        # Only applies to authenticated users
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return None

        # Django stores the session expiry time as a key in the session
        # (via SESSION_SAVE_EVERY_REQUEST + SESSION_COOKIE_AGE).
        # We check the real remaining time from the session backend.
        session = request.session
        cookie_age = getattr(settings, 'SESSION_COOKIE_AGE', 7200)

        # _session_expiry is set by Django to an epoch timestamp when using
        # set_expiry(). For the standard cookie-age flow we calculate from
        # the session's last-modified time stored as '_last_activity'.
        last_activity = session.get('_last_activity')
        now = time.time()

        if last_activity is None:
            # First request after login — stamp it
            session['_last_activity'] = now
            return None

        elapsed = now - last_activity
        if elapsed >= cookie_age:
            username = request.user.username
            logger.info(
                "Session expired for user '%s' after %ds of inactivity (IP: %s)",
                username, elapsed, _get_client_ip(request),
            )
            auth_logout(request)
            request.session.flush()

            # Determine redirect: admin goes back to admin login
            if path.startswith('/admin/'):
                return redirect('/admin/login/?next=' + path + '&expired=1')

            login_url = getattr(settings, 'LOGIN_URL', '/accounts/login/')
            return redirect(f'{login_url}?next={path}&expired=1')

        # Sliding window — refresh last activity on every request
        session['_last_activity'] = now
        return None
