from django.db import models
from django.contrib.auth.models import User


class ScanResult(models.Model):
    """Model to store skin scan analysis results"""

    GENDER_CHOICES = [
        ('male',   'Male'),
        ('female', 'Female'),
        ('other',  'Other / Prefer not to say'),
    ]

    SKIN_TONE_CHOICES = [
        ('fair', 'Fair'),
        ('light', 'Light'),
        ('medium', 'Medium'),
        ('tan', 'Tan'),
        ('deep', 'Deep'),
    ]
    
    UNDERTONE_CHOICES = [
        ('warm', 'Warm'),
        ('cool', 'Cool'),
        ('neutral', 'Neutral'),
        ('olive', 'Olive'),
    ]
    
    SKIN_TYPE_CHOICES = [
        ('oily', 'Oily'),
        ('dry', 'Dry'),
        ('combination', 'Combination'),
        ('normal', 'Normal'),
    ]
    
    FACE_SHAPE_CHOICES = [
        ('oval', 'Oval'),
        ('round', 'Round'),
        ('square', 'Square'),
        ('heart', 'Heart'),
        ('oblong', 'Oblong'),
        ('rectangle', 'Rectangle'),
        ('diamond', 'Diamond'),
        ('triangle', 'Triangle'),
    ]
    
    # User and session
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='scans')
    session_key = models.CharField(max_length=100, blank=True)
    is_demo = models.BooleanField(default=False)

    # Gender
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='female')
    
    # Image
    scan_image = models.ImageField(upload_to='scans/%Y/%m/%d/', null=True, blank=True)
    
    # Basic attributes
    skin_tone = models.CharField(max_length=20, choices=SKIN_TONE_CHOICES, default='medium')
    undertone = models.CharField(max_length=20, choices=UNDERTONE_CHOICES, default='neutral')
    face_shape = models.CharField(max_length=20, choices=FACE_SHAPE_CHOICES, default='oval')
    skin_type = models.CharField(max_length=20, choices=SKIN_TYPE_CHOICES, default='normal')
    
    # Ages
    skin_age = models.IntegerField(default=25)
    real_age = models.IntegerField(default=25)  # updated by post-scan questionnaire
    
    # Scores (0-100)
    harmony_score = models.IntegerField(default=75)
    hydration_score = models.IntegerField(default=60)
    pigmentation_score = models.IntegerField(default=30)
    acne_score = models.IntegerField(default=20)
    aging_score = models.IntegerField(default=25)
    elasticity_score = models.IntegerField(default=65)
    
    # HuggingFace API results
    hf_acne_severity = models.CharField(max_length=20, default='none')  # none/mild/moderate/severe
    hf_skin_type = models.CharField(max_length=20, default='normal')
    hf_undertone = models.CharField(max_length=20, default='neutral')
    
    hf_acne_confidence = models.FloatField(default=0.0)
    hf_skin_type_confidence = models.FloatField(default=0.0)
    hf_undertone_confidence = models.FloatField(default=0.0)
    
    hf_acne_raw = models.TextField(blank=True)
    hf_skin_type_raw = models.TextField(blank=True)
    hf_undertone_raw = models.TextField(blank=True)
    
    # Facial zones (JSON field)
    facial_zones = models.JSONField(default=dict, blank=True)
    
    # Detected concerns (Many-to-Many with SkinConcern)
    detected_concerns = models.ManyToManyField('products.SkinConcern', blank=True, related_name='scans')
    
    # ── Post-scan questionnaire answers (improves accuracy) ──────────────────
    # real_age (declared above in # Ages section) is updated by the questionnaire
    qa_age        = models.IntegerField(null=True, blank=True)
    qa_water_intake  = models.CharField(max_length=20, blank=True)  # low / moderate / high
    qa_sleep_hours   = models.CharField(max_length=20, blank=True)  # <6 / 6-8 / >8
    qa_stress_level  = models.CharField(max_length=20, blank=True)  # low / moderate / high
    qa_diet          = models.CharField(max_length=20, blank=True)  # balanced / oily / sugary
    qa_outdoor_hours = models.CharField(max_length=20, blank=True)  # low / moderate / high
    qa_skin_concerns = models.JSONField(default=list, blank=True)   # user-selected concerns
    qa_completed     = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        if self.user:
            return f"{self.user.username} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
        return f"Anonymous - {self.created_at.strftime('%Y-%m-%d %H:%M')}"


class ProgressComparison(models.Model):
    """Stores computed comparison between two ScanResult objects."""

    VERDICT_CHOICES = [
        ('improved',  'Improved'),
        ('unchanged', 'Unchanged'),
        ('declined',  'Declined'),
    ]

    user            = models.ForeignKey(User, on_delete=models.CASCADE,
                                        null=True, blank=True,
                                        related_name='progress_comparisons')
    baseline_scan   = models.ForeignKey(ScanResult, on_delete=models.CASCADE,
                                        related_name='as_baseline')
    latest_scan     = models.ForeignKey(ScanResult, on_delete=models.CASCADE,
                                        related_name='as_latest')

    # Deltas (latest - baseline; positive = increase)
    harmony_delta      = models.IntegerField(default=0)
    hydration_delta    = models.IntegerField(default=0)
    acne_delta         = models.IntegerField(default=0,
                                             help_text='Positive = more acne (worse); negative = improvement')
    pigmentation_delta = models.IntegerField(default=0)
    aging_delta        = models.IntegerField(default=0)
    elasticity_delta   = models.IntegerField(default=0)

    days_between       = models.IntegerField(default=0)

    ai_verdict         = models.CharField(max_length=20, choices=VERDICT_CHOICES,
                                          default='unchanged')
    ai_recommendation  = models.TextField(blank=True)

    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Progress Comparison'

    def __str__(self):
        u = self.user.username if self.user else 'anon'
        return f"{u}: {self.baseline_scan_id} → {self.latest_scan_id} [{self.ai_verdict}]"