"""
Notification views — list, mark read, mark all read, delete.
"""
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.http import require_POST

from .models import Notification


@login_required
def notification_list(request):
    """GET /notifications/ — show all notifications for the logged-in user."""
    notifs = Notification.objects.filter(user=request.user).order_by('-created_at')
    unread_count = notifs.filter(is_read=False).count()

    # Auto-mark all as read when user opens the page
    notifs.filter(is_read=False).update(is_read=True)

    return render(request, 'notifications/list.html', {
        'notifications': notifs,
        'unread_count':  unread_count,
    })


@login_required
@require_POST
def mark_read(request, pk):
    """AJAX POST — mark a single notification as read."""
    notif = get_object_or_404(Notification, pk=pk, user=request.user)
    notif.is_read = True
    notif.save(update_fields=['is_read'])
    return JsonResponse({'ok': True})


@login_required
@require_POST
def mark_all_read(request):
    """AJAX POST — mark all notifications as read."""
    Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return JsonResponse({'ok': True, 'count': 0})


@login_required
@require_POST
def delete_notification(request, pk):
    """AJAX POST — delete a single notification."""
    notif = get_object_or_404(Notification, pk=pk, user=request.user)
    notif.delete()
    return JsonResponse({'ok': True})


@login_required
def unread_count(request):
    """AJAX GET — return unread count (used by nav badge polling)."""
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})
