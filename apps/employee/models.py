from django.db import models
from django.contrib.auth.models import User


class EmployeeLoginLog(models.Model):
    """Tracks each login and logout event for staff/employee accounts."""
    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_logs')
    event      = models.CharField(max_length=10, choices=[('login', 'Login'), ('logout', 'Logout')])
    timestamp  = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True, default='')
    session_key = models.CharField(max_length=64, blank=True, default='')

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'User Login Log'
        verbose_name_plural = 'User Login Logs'

    def __str__(self):
        return f"{self.user.username} — {self.event} at {self.timestamp:%d %b %Y %H:%M}"
