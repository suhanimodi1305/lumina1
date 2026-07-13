"""
Progress signals — auto-create ScanMilestone and send scan reminders.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone


@receiver(post_save, sender='scanner.ScanResult')
def handle_new_scan(sender, instance, created, **kwargs):
    """When a real scan is saved, link it to the user's scan milestone."""
    if not created or instance.is_demo or instance.user is None:
        return

    try:
        from apps.progress.models import ScanMilestone
        from apps.notifications.models import Notification

        milestone, is_new = ScanMilestone.objects.get_or_create(
            user=instance.user,
            defaults={'started_at': timezone.now()},
        )

        # Link Day 0 scan
        if milestone.scan_day0 is None:
            milestone.scan_day0  = instance
            milestone.score_day0 = instance.harmony_score
            milestone.save(update_fields=['scan_day0', 'score_day0'])

            # Schedule Day 14 reminder notification
            Notification.create_for_user(
                user=instance.user,
                notif_type='scan_reminder',
                title='Your Day 14 Scan is Scheduled 📅',
                message='Come back in 14 days for your first progress comparison scan. We\'ll remind you!',
                icon='📸',
                action_url='/progress/milestones/',
                action_label='View Milestones',
            )

    except Exception:
        pass  # never break the scan flow
