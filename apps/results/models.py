from django.db import models
from apps.scanner.models import ScanResult as ScannerScanResult

class ScanResult(models.Model):
    """Model to store analysis results"""
    scan_result = models.OneToOneField(ScannerScanResult,on_delete=models.CASCADE,related_name='result')
    
    # Skin analysis
    skin_type = models.CharField(max_length=50, blank=True)
    acne_severity = models.CharField(max_length=50, blank=True)
    undertone = models.CharField(max_length=50, blank=True)
    
    # Facial zones
    forehead_severity = models.CharField(max_length=20, default='none')
    nose_severity = models.CharField(max_length=20, default='none')
    left_cheek_severity = models.CharField(max_length=20, default='none')
    right_cheek_severity = models.CharField(max_length=20, default='none')
    chin_severity = models.CharField(max_length=20, default='none')
    
    # Scores
    overall_score = models.IntegerField(default=0)
    skin_health_score = models.IntegerField(default=0)
    hydration_score = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
     if self.scan_result.user:
        return f"Results for {self.scan_result.user.username}"
     return "Results"