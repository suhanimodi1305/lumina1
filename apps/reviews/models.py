"""
Reviews app — product reviews with skin type, verification, and moderation.
"""
from django.db import models
from django.contrib.auth.models import User
from apps.products.models import Product


class ProductReview(models.Model):
    """User review for a product, optionally verified by purchase."""

    STATUS_CHOICES = [
        ('pending',   'Pending Approval'),
        ('approved',  'Approved'),
        ('rejected',  'Rejected'),
        ('flagged',   'Flagged'),
    ]

    SKIN_TYPE_CHOICES = [
        ('oily',        'Oily'),
        ('dry',         'Dry'),
        ('combination', 'Combination'),
        ('normal',      'Normal'),
        ('sensitive',   'Sensitive'),
    ]

    CONCERN_CHOICES = [
        ('acne',        'Acne'),
        ('pigmentation','Pigmentation'),
        ('dryness',     'Dryness'),
        ('aging',       'Aging'),
        ('dullness',    'Dullness'),
        ('sensitivity', 'Sensitivity'),
    ]

    # Core
    product     = models.ForeignKey(Product, on_delete=models.CASCADE,
                                    related_name='reviews')
    user        = models.ForeignKey(User, on_delete=models.CASCADE,
                                    related_name='product_reviews')
    rating      = models.PositiveSmallIntegerField(
        help_text='1–5 star rating'
    )

    # Review content
    title       = models.CharField(max_length=200)
    body        = models.TextField(max_length=2000)

    # User context (helps others find relevant reviews)
    skin_type   = models.CharField(max_length=20, choices=SKIN_TYPE_CHOICES, blank=True)
    concern     = models.CharField(max_length=20, choices=CONCERN_CHOICES, blank=True)
    used_for_weeks = models.PositiveSmallIntegerField(
        default=0, help_text='How many weeks the user used this product'
    )

    # Would recommend?
    would_recommend = models.BooleanField(default=True)

    # AI scan data used? (links to actual scan for credibility)
    scan_verified = models.BooleanField(
        default=False,
        help_text='Review linked to user\'s AI skin scan — adds verified badge'
    )

    # Verification: linked to an order
    purchase_verified = models.BooleanField(default=False)

    # Moderation
    status      = models.CharField(max_length=12, choices=STATUS_CHOICES, default='pending')
    flagged_reason = models.CharField(max_length=200, blank=True)

    # Helpfulness votes
    helpful_count = models.PositiveIntegerField(default=0)

    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('product', 'user')   # one review per product per user
        ordering = ['-created_at']
        verbose_name = 'Product Review'

    def __str__(self):
        return f'{self.user.username} → {self.product.name} ({self.rating}★)'

    @property
    def star_display(self):
        return '★' * self.rating + '☆' * (5 - self.rating)


class ReviewHelpful(models.Model):
    """Track who marked a review as helpful (prevent duplicate votes)."""
    review  = models.ForeignKey(ProductReview, on_delete=models.CASCADE,
                                related_name='helpful_votes')
    user    = models.ForeignKey(User, on_delete=models.CASCADE)
    voted_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('review', 'user')
