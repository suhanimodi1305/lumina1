"""
Progress Tracking models.
Covers: daily routine log, weekly check-in, scan milestones (Day 0/14/30/60/90).
"""
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


# ─────────────────────────────────────────────────────────────────────────────
# DAILY ROUTINE LOG
# ─────────────────────────────────────────────────────────────────────────────

class DailyRoutineLog(models.Model):
    """Tracks whether a user completed their AM/PM routine each day."""

    user         = models.ForeignKey(User, on_delete=models.CASCADE,
                                     related_name='daily_routine_logs')
    log_date     = models.DateField()

    # AM routine
    am_done      = models.BooleanField(default=False)
    am_notes     = models.CharField(max_length=300, blank=True)
    am_logged_at = models.DateTimeField(null=True, blank=True)

    # PM routine
    pm_done      = models.BooleanField(default=False)
    pm_notes     = models.CharField(max_length=300, blank=True)
    pm_logged_at = models.DateTimeField(null=True, blank=True)

    # Water intake
    water_glasses = models.PositiveSmallIntegerField(default=0)

    # SPF reapplication
    spf_applied   = models.BooleanField(default=False)

    # Self-rated skin today (1–5)
    skin_rating   = models.PositiveSmallIntegerField(
        default=3,
        help_text='User self-rated skin condition 1 (poor) – 5 (great)'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'log_date')
        ordering = ['-log_date']
        verbose_name = 'Daily Routine Log'

    def __str__(self):
        status = 'AM+PM' if (self.am_done and self.pm_done) else 'AM' if self.am_done else 'PM' if self.pm_done else '—'
        return f'{self.user.username} | {self.log_date} | {status}'

    @property
    def fully_complete(self):
        return self.am_done and self.pm_done

    @property
    def points_earned(self):
        pts = 0
        if self.am_done:   pts += 10
        if self.pm_done:   pts += 10
        if self.spf_applied: pts += 5
        if self.water_glasses >= 8: pts += 5
        return pts


# ─────────────────────────────────────────────────────────────────────────────
# WEEKLY CHECK-IN
# ─────────────────────────────────────────────────────────────────────────────

class WeeklyCheckin(models.Model):
    """User's weekly skin check-in questionnaire."""

    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]  # 1–5

    user        = models.ForeignKey(User, on_delete=models.CASCADE,
                                    related_name='weekly_checkins')
    week_number = models.PositiveSmallIntegerField(
        help_text='Weeks since the user started (1-indexed)'
    )
    week_start  = models.DateField()

    # Skin ratings this week (1–5)
    overall_rating      = models.PositiveSmallIntegerField(choices=RATING_CHOICES, default=3)
    hydration_rating    = models.PositiveSmallIntegerField(choices=RATING_CHOICES, default=3)
    acne_rating         = models.PositiveSmallIntegerField(choices=RATING_CHOICES, default=3,
                                                           help_text='5 = no acne, 1 = very bad')
    brightness_rating   = models.PositiveSmallIntegerField(choices=RATING_CHOICES, default=3)

    # Products used this week (JSON list of product names/SKUs)
    products_used       = models.JSONField(default=list, blank=True)

    # Any new concerns noticed?
    new_concerns        = models.CharField(max_length=500, blank=True)
    notes               = models.TextField(blank=True)

    # Did user take a comparison selfie?
    has_selfie          = models.BooleanField(default=False)

    # Computed week-on-week delta from previous check-in
    overall_delta       = models.SmallIntegerField(default=0)

    completed_at        = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'week_number')
        ordering = ['-week_number']
        verbose_name = 'Weekly Check-in'

    def __str__(self):
        return f'{self.user.username} — Week {self.week_number} ({self.week_start})'


# ─────────────────────────────────────────────────────────────────────────────
# SCAN MILESTONE SCHEDULE
# ─────────────────────────────────────────────────────────────────────────────

class ScanMilestone(models.Model):
    """
    Tracks the user's scan journey: Day 0, Day 14, Day 30, Day 60, Day 90.
    One ScanMilestone per user, auto-created when they complete their first scan.
    """

    MILESTONE_DAYS = [0, 14, 30, 60, 90]

    user            = models.OneToOneField(User, on_delete=models.CASCADE,
                                           related_name='scan_milestone')
    started_at      = models.DateTimeField(auto_now_add=True)

    # Linked scan IDs for each milestone (null = not yet done)
    scan_day0       = models.ForeignKey(
        'scanner.ScanResult', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='milestone_day0'
    )
    scan_day14      = models.ForeignKey(
        'scanner.ScanResult', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='milestone_day14'
    )
    scan_day30      = models.ForeignKey(
        'scanner.ScanResult', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='milestone_day30'
    )
    scan_day60      = models.ForeignKey(
        'scanner.ScanResult', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='milestone_day60'
    )
    scan_day90      = models.ForeignKey(
        'scanner.ScanResult', null=True, blank=True, on_delete=models.SET_NULL,
        related_name='milestone_day90'
    )

    # Harmony scores at each milestone (cached for quick chart rendering)
    score_day0      = models.IntegerField(null=True, blank=True)
    score_day14     = models.IntegerField(null=True, blank=True)
    score_day30     = models.IntegerField(null=True, blank=True)
    score_day60     = models.IntegerField(null=True, blank=True)
    score_day90     = models.IntegerField(null=True, blank=True)

    updated_at      = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Scan Milestone'

    def __str__(self):
        return f'{self.user.username} — Day 0: {self.started_at:%d %b %Y}'

    @property
    def days_since_start(self):
        from datetime import date
        return (date.today() - self.started_at.date()).days

    @property
    def next_milestone_day(self):
        """Returns the next scan milestone day the user hasn't completed yet."""
        completed = self.completed_milestones
        for d in self.MILESTONE_DAYS:
            if d not in completed:
                return d
        return None

    @property
    def completed_milestones(self):
        """Returns list of completed milestone days."""
        done = []
        for d, fk in [
            (0,  self.scan_day0),
            (14, self.scan_day14),
            (30, self.scan_day30),
            (60, self.scan_day60),
            (90, self.scan_day90),
        ]:
            if fk is not None:
                done.append(d)
        return done

    @property
    def transformation_pct(self):
        """Percentage improvement from Day 0 to latest milestone."""
        if self.score_day0 and self.score_day0 > 0:
            latest = self.score_day90 or self.score_day60 or self.score_day30 or self.score_day14
            if latest:
                return round(((latest - self.score_day0) / self.score_day0) * 100, 1)
        return 0
