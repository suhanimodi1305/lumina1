from django.db import models
from django.contrib.auth.models import User
import uuid


class Conversation(models.Model):
    """Chat conversation with Dr. Lumina"""

    # Chat mode / tab types
    MODE_DOCTOR = 'doctor'
    MODE_MAKEUP = 'makeup'
    MODE_KBEAUTY = 'kbeauty'
    MODE_CHOICES = [
        (MODE_DOCTOR,  'AI Doctor'),
        (MODE_MAKEUP,  'Makeup'),
        (MODE_KBEAUTY, 'K-Beauty'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='conversations')
    title = models.CharField(max_length=200, default='New Consultation')
    mode = models.CharField(max_length=20, choices=MODE_CHOICES, default=MODE_DOCTOR)

    # Optional link to scan result
    skin_scan = models.ForeignKey(
        'scanner.ScanResult',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='chat_conversations'
    )

    is_vip_session = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.user.username} - {self.title}"

    def message_count(self):
        return self.messages.count()

    def last_message(self):
        return self.messages.last()


class Message(models.Model):
    """Individual message in a conversation"""
    ROLE_CHOICES = [
        ('user', 'User'),
        ('assistant', 'Assistant'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    content = models.TextField()
    
    # Optional image data (base64)
    image_data = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}"


class QuickPrompt(models.Model):
    """Quick prompts for common questions"""
    prompt_text = models.CharField(max_length=200)
    category = models.CharField(max_length=50, blank=True)
    order = models.IntegerField(default=0)
    active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['order', 'prompt_text']
    
    def __str__(self):
        return self.prompt_text