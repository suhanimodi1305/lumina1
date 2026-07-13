"""
Diagnostic app models — Wizard sessions, habit logs, marketing referral stats.
"""
from django.db import models
from django.contrib.auth.models import User
import uuid


# ─────────────────────────────────────────────────────────────────
# DIAGNOSTIC SESSION (one per quiz completion)
# ─────────────────────────────────────────────────────────────────

class DiagnosticSession(models.Model):
    """Stores one completed diagnostic wizard run."""

    TIER_CHOICES = [
        ('normal', 'Normal'),
        ('medium', 'Medium'),
        ('vip',    'VIP'),
    ]

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user        = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='diagnostic_sessions')
    session_key = models.CharField(max_length=100, blank=True)

    # Step 1 — category tokens selected (JSON list)
    selected_categories = models.JSONField(default=list)

    # Step 2 — skin profile
    skin_type   = models.CharField(max_length=30, blank=True)
    concern_1   = models.CharField(max_length=60, blank=True)
    concern_2   = models.CharField(max_length=60, blank=True)
    concern_3   = models.CharField(max_length=60, blank=True)
    budget      = models.CharField(max_length=20, blank=True)   # low / mid / high

    # Step 3 — lifestyle sliders (1-10)
    water_intake  = models.PositiveSmallIntegerField(default=5)
    sleep_hours   = models.PositiveSmallIntegerField(default=6)
    stress_level  = models.PositiveSmallIntegerField(default=5)

    # Recommended tier (computed on submit)
    recommended_tier = models.CharField(max_length=10, choices=TIER_CHOICES, default='normal')

    completed   = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Diagnostic Session'

    def __str__(self):
        user_str = self.user.username if self.user else 'anon'
        return f"[{self.recommended_tier.upper()}] {user_str} — {self.created_at:%d %b %Y}"


# ─────────────────────────────────────────────────────────────────
# HABIT LOG (Log & Earn)
# ─────────────────────────────────────────────────────────────────

class HabitCategory(models.Model):
    """Predefined habit categories for the Log & Earn board."""
    slug        = models.SlugField(unique=True)
    title       = models.CharField(max_length=80)
    icon        = models.CharField(max_length=10)          # emoji
    color_class = models.CharField(max_length=30)          # CSS class suffix
    points      = models.PositiveSmallIntegerField(default=5)
    description = models.CharField(max_length=200, blank=True)
    order       = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


class HabitLog(models.Model):
    """One log entry by a user for a habit."""
    user        = models.ForeignKey(User, on_delete=models.CASCADE, related_name='habit_logs')
    habit       = models.ForeignKey(HabitCategory, on_delete=models.CASCADE, related_name='logs')
    notes       = models.CharField(max_length=200, blank=True)
    points_earned = models.PositiveSmallIntegerField(default=0)
    logged_at   = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-logged_at']
        verbose_name = 'Habit Log'

    def __str__(self):
        return f"{self.user.username} logged {self.habit.title} (+{self.points_earned}pts)"


# ─────────────────────────────────────────────────────────────────
# MARKETING REFERRAL CLICK TRACKING
# ─────────────────────────────────────────────────────────────────

class ReferralClick(models.Model):
    """Tracks every click on a referral link that leads to the diagnostic quiz."""
    referral_code = models.CharField(max_length=20)
    ip_address    = models.GenericIPAddressField(null=True, blank=True)
    user_agent    = models.TextField(blank=True)
    converted     = models.BooleanField(default=False)   # True when quiz completed
    clicked_at    = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-clicked_at']

    def __str__(self):
        status = 'converted' if self.converted else 'click'
        return f"[{status}] {self.referral_code} @ {self.clicked_at:%d %b %H:%M}"


# ─────────────────────────────────────────────────────────────────
# SMART DIAGNOSTIC SESSION — AI-driven dynamic questionnaire
# ─────────────────────────────────────────────────────────────────

class SmartDiagSession(models.Model):
    """Stores one Smart Diagnostic quiz run — dynamic question flow."""

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user        = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='smart_diag_sessions')
    session_key = models.CharField(max_length=100, blank=True)

    # Step 1 — primary goal
    primary_goal = models.CharField(max_length=40, blank=True)

    # Skin answers (JSON — stores all multi-choice answers)
    answers      = models.JSONField(default=dict)

    # Analysis output (JSON — computed result)
    analysis     = models.JSONField(default=dict)

    # Computed fields for quick querying
    severity        = models.CharField(max_length=20, blank=True)     # minimal/mild/moderate/severe
    top_concern_cat = models.CharField(max_length=40, blank=True)     # acne/pigment/aging/etc.

    completed   = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Smart Diagnostic Session'

    def __str__(self):
        user_str = self.user.username if self.user else 'anon'
        return f"[{self.primary_goal or 'incomplete'}] {user_str} — {self.created_at:%d %b %Y}"
