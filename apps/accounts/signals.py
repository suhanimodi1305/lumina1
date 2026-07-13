"""
Accounts signals — auto-record login history on successful login.
"""
from django.contrib.auth.signals import user_logged_in
from django.dispatch import receiver


@receiver(user_logged_in)
def on_user_login(sender, request, user, **kwargs):
    """Record login history and device fingerprint on every successful login."""
    from .views import _record_login
    _record_login(user, request)
