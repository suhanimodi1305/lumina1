"""
Signals to automatically log login/logout events for all users.
Security hardening:
  - IP extraction uses last X-Forwarded-For hop (set by trusted reverse proxy),
    not the first hop which a client can spoof.
  - User-agent capped at 500 chars to prevent log injection.
"""
import logging
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from .models import EmployeeLoginLog

logger = logging.getLogger(__name__)


def _get_client_ip(request) -> str:
    """
    Extract the real client IP.

    When behind a trusted reverse proxy (nginx/gunicorn), the proxy appends
    the client's real IP to X-Forwarded-For.  Taking the LAST entry prevents
    a client from spoofing their IP by sending a crafted X-Forwarded-For header.

    If you run multiple proxies, adjust the -1 index accordingly.
    """
    xff = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if xff:
        # Last entry = added by your trusted proxy
        return xff.split(',')[-1].strip()
    return request.META.get('REMOTE_ADDR', '')


def _sanitize_user_agent(ua: str) -> str:
    """Remove newlines from UA to prevent log injection, cap at 500 chars."""
    return ua.replace('\n', ' ').replace('\r', ' ')[:500]


@receiver(user_logged_in)
def log_login(sender, request, user, **kwargs):
    ip = _get_client_ip(request)
    logger.info("Login | user=%s ip=%s", user.username, ip)
    EmployeeLoginLog.objects.create(
        user        = user,
        event       = 'login',
        ip_address  = ip or None,
        user_agent  = _sanitize_user_agent(request.META.get('HTTP_USER_AGENT', '')),
        session_key = request.session.session_key or '',
    )


@receiver(user_logged_out)
def log_logout(sender, request, user, **kwargs):
    if user:
        ip = _get_client_ip(request)
        logger.info("Logout | user=%s ip=%s", user.username, ip)
        EmployeeLoginLog.objects.create(
            user        = user,
            event       = 'logout',
            ip_address  = ip or None,
            user_agent  = _sanitize_user_agent(request.META.get('HTTP_USER_AGENT', '')),
            session_key = request.session.session_key or '',
        )
