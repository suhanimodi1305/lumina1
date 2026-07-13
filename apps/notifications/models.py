"""
Notifications app — user-facing alerts, system events, skin scan reminders.
"""
from django.db import models
from django.contrib.auth.models import User


class Notification(models.Model):
    """
    A user-facing notification (scan reminder, tier change, order update, etc.)
    """
    TYPE_CHOICES = [
        ('scan_reminder',   'Scan Reminder'),
        ('progress_check',  'Progress Check-in'),
        ('tier_upgrade',    'Tier Upgrade'),
        ('tier_expiry',     'Tier Expiry Warning'),
        ('order_update',    'Order Update'),
        ('points_earned',   'Points Earned'),
        ('routine_reminder','Routine Reminder'),
        ('weekly_checkin',  'Weekly Check-in'),
        ('system',          'System Message'),
        ('achievement',     'Achievement Unlocked'),
    ]

    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notif_type  = models.CharField(max_length=30, choices=TYPE_CHOICES, default='system')
    title       = models.CharField(max_length=200)
    message     = models.TextField()
    icon        = models.CharField(max_length=10, default='🔔')    # emoji icon
    action_url  = models.CharField(max_length=300, blank=True)     # optional link
    action_label= models.CharField(max_length=100, blank=True)     # button label
    is_read     = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Notification'

    def __str__(self):
        return f'[{self.notif_type}] {self.user.username}: {self.title[:50]}'

    @classmethod
    def create_for_user(cls, user, notif_type, title, message, icon='🔔',
                        action_url='', action_label=''):
        """Convenience factory — creates and returns a notification."""
        return cls.objects.create(
            user=user, notif_type=notif_type, title=title, message=message,
            icon=icon, action_url=action_url, action_label=action_label,
        )
