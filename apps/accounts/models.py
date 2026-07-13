"""
Accounts models — email history, saved addresses, login history, devices.
"""
from django.db import models
from django.contrib.auth.models import User


# ─────────────────────────────────────────────────────────────────────────────
# SAVED ADDRESSES
# ─────────────────────────────────────────────────────────────────────────────

class SavedAddress(models.Model):
    """Persistent delivery addresses for a customer."""
    ADDRESS_TYPE_CHOICES = [
        ('home',   'Home'),
        ('work',   'Work'),
        ('other',  'Other'),
    ]

    user          = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_addresses')
    label         = models.CharField(max_length=20, choices=ADDRESS_TYPE_CHOICES, default='home')
    full_name     = models.CharField(max_length=150)
    phone         = models.CharField(max_length=15)
    address_line1 = models.CharField(max_length=250)
    address_line2 = models.CharField(max_length=250, blank=True)
    city          = models.CharField(max_length=100)
    state         = models.CharField(max_length=100)
    pincode       = models.CharField(max_length=10)
    is_default    = models.BooleanField(default=False)
    created_at    = models.DateTimeField(auto_now_add=True)
    updated_at    = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_default', '-created_at']
        verbose_name = 'Saved Address'

    def __str__(self):
        return f'{self.user.username} — {self.get_label_display()} ({self.city})'

    def save(self, *args, **kwargs):
        # Ensure only one default per user
        if self.is_default:
            SavedAddress.objects.filter(user=self.user, is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


# ─────────────────────────────────────────────────────────────────────────────
# LOGIN HISTORY
# ─────────────────────────────────────────────────────────────────────────────

class LoginHistory(models.Model):
    """Tracks every successful login event per user."""
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_history')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    device_type = models.CharField(max_length=20, blank=True)   # mobile / desktop / tablet
    browser    = models.CharField(max_length=80, blank=True)
    os         = models.CharField(max_length=80, blank=True)
    city       = models.CharField(max_length=80, blank=True)
    country    = models.CharField(max_length=80, blank=True)
    logged_in_at = models.DateTimeField(auto_now_add=True)
    was_suspicious = models.BooleanField(default=False)  # flag for new location/device

    class Meta:
        ordering = ['-logged_in_at']
        verbose_name = 'Login History'
        verbose_name_plural = 'Login History'

    def __str__(self):
        return f'{self.user.username} — {self.ip_address} @ {self.logged_in_at:%d %b %Y %H:%M}'


# ─────────────────────────────────────────────────────────────────────────────
# USER DEVICES
# ─────────────────────────────────────────────────────────────────────────────

class UserDevice(models.Model):
    """Tracks unique devices that have logged into a user's account."""
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices')
    device_name = models.CharField(max_length=150)     # e.g. "Chrome on Windows"
    device_type = models.CharField(max_length=20, blank=True)  # mobile/desktop/tablet
    browser     = models.CharField(max_length=80, blank=True)
    os          = models.CharField(max_length=80, blank=True)
    ip_address  = models.GenericIPAddressField(null=True, blank=True)
    user_agent  = models.TextField(blank=True)
    first_seen  = models.DateTimeField(auto_now_add=True)
    last_seen   = models.DateTimeField(auto_now=True)
    is_trusted  = models.BooleanField(default=False)
    is_current  = models.BooleanField(default=False)

    class Meta:
        ordering = ['-last_seen']
        verbose_name = 'User Device'

    def __str__(self):
        return f'{self.user.username} — {self.device_name}'


# ─────────────────────────────────────────────────────────────────────────────
# EMAIL LOG
# ─────────────────────────────────────────────────────────────────────────────

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
