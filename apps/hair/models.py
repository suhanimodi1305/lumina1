"""
Hair Diagnosis app models.
"""
from django.db import models
from django.contrib.auth.models import User
import uuid


class HairSession(models.Model):
    """Stores one completed hair diagnostic wizard run."""

    SEVERITY_CHOICES = [
        ('stage1', 'Stage 1 — Mild'),
        ('stage2', 'Stage 2 — Moderate'),
        ('stage3', 'Stage 3 — Significant'),
        ('stage4', 'Stage 4 — Severe'),
    ]

    PLAN_CHOICES = [
        ('basic',    'Basic'),
        ('advanced', 'Advanced'),
        ('premium',  'Premium'),
    ]

    id          = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user        = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='hair_sessions')
    session_key = models.CharField(max_length=100, blank=True)

    # Q1 — hair concern type (JSON list, multi-select)
    hair_concerns = models.JSONField(default=list)

    # Q2 — scalp condition
    scalp_condition = models.CharField(max_length=50, blank=True)

    # Q3 — root cause symptoms (JSON list)
    root_symptoms = models.JSONField(default=list)

    # Q4 — hair type & texture
    hair_type    = models.CharField(max_length=30, blank=True)
    hair_texture = models.CharField(max_length=30, blank=True)

    # Q5 — severity stage
    severity_stage = models.CharField(max_length=20, blank=True)

    # Q6 — lifestyle details
    first_name   = models.CharField(max_length=80, blank=True)
    gender       = models.CharField(max_length=20, blank=True)
    water_intake = models.CharField(max_length=20, blank=True)   # low / moderate / high
    sleep_quality= models.CharField(max_length=20, blank=True)   # lt6 / 6to8 / gt8

    # Computed recommended plan
    recommended_plan = models.CharField(max_length=20, choices=PLAN_CHOICES, default='basic')

    completed   = models.BooleanField(default=False)
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Hair Session'

    def __str__(self):
        user_str = self.user.username if self.user else 'anon'
        return f"[{self.recommended_plan.upper()}] {user_str} — {self.created_at:%d %b %Y}"
