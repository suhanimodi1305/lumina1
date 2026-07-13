"""
Notification context processor — injects unread count into every template.
"""
from .models import Notification


def unread_notifications(request):
    """Adds `unread_notif_count` to every template context."""
    if not request.user.is_authenticated:
        return {'unread_notif_count': 0}
    try:
        count = Notification.objects.filter(
            user=request.user, is_read=False
        ).count()
    except Exception:
        count = 0
    return {'unread_notif_count': count}
