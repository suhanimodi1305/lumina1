"""
Accounts models — email history log for admin visibility.
"""
from django.db import models
from django.contrib.auth.models import User


class EmailLog(models.Model):
    """
    Tracks every outbound email sent by Lumina (password resets, notifications, etc.).
    Visible in Django admin under Accounts → Email Logs.
    """
    EMAIL_TYPE_CHOICES = [
        ('password_reset', 'Password Reset'),
        ('welcome',        'Welcome Email'),
        ('notification',   'Notification'),
        ('other',          'Other'),
    ]

    STATUS_CHOICES = [
        ('sent',    'Sent'),
        ('failed',  'Failed'),
        ('pending', 'Pending'),
    ]

    user        = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='email_logs',
        help_text='The user this email was sent to (if known).'
    )
    email_type  = models.CharField(max_length=32, choices=EMAIL_TYPE_CHOICES, default='other')
    recipient   = models.EmailField(help_text='Recipient email address.')
    subject     = models.CharField(max_length=255)
    body_preview= models.TextField(
        blank=True,
        help_text='First 500 chars of the email body (for admin preview).'
    )
    status      = models.CharField(max_length=16, choices=STATUS_CHOICES, default='sent')
    error_msg   = models.TextField(blank=True, help_text='Error detail if sending failed.')
    sent_at     = models.DateTimeField(auto_now_add=True)
    ip_address  = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-sent_at']
        verbose_name = 'Email Log'
        verbose_name_plural = 'Email Logs'

    def __str__(self):
        return f'[{self.get_email_type_display()}] → {self.recipient} ({self.sent_at:%Y-%m-%d %H:%M})'
