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
    real_age = models.IntegerField(default=25)
    
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
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        if self.user:
            return f"{self.user.username} - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
        return f"Anonymous - {self.created_at.strftime('%Y-%m-%d %H:%M')}"