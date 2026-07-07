"""
Products app models - Korean skincare and makeup products
"""
from django.db import models


class SkinConcern(models.Model):
    """Skin concerns/conditions that products can address"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        verbose_name = 'Skin Concern'
        verbose_name_plural = 'Skin Concerns'
    
    def __str__(self):
        return self.name


class Product(models.Model):
    """Unified product model for Korean skincare and makeup"""
    
    CATEGORY_CHOICES = [
        # Skincare categories
        ('cleanser', 'Cleanser'),
        ('toner', 'Toner'),
        ('essence', 'Essence'),
        ('serum', 'Serum'),
        ('ampoule', 'Ampoule'),
        ('moisturizer', 'Moisturizer'),
        ('cream', 'Cream'),
        ('emulsion', 'Emulsion'),
        ('sunscreen', 'Sunscreen'),
        ('mask', 'Mask'),
        ('eye_cream', 'Eye Cream'),
        ('exfoliator', 'Exfoliator'),
        ('oil', 'Oil'),
        ('mist', 'Mist'),
        ('treatment', 'Treatment'),
        
        # Makeup categories
        ('primer', 'Primer'),
        ('foundation', 'Foundation'),
        ('concealer', 'Concealer'),
        ('setting_powder', 'Setting Powder'),
        ('powder', 'Powder'),
        ('blush', 'Blush'),
        ('bronzer', 'Bronzer'),
        ('highlighter', 'Highlighter'),
        ('eyeshadow', 'Eyeshadow'),
        ('eyeshadow_palette', 'Eyeshadow Palette'),
        ('eyeliner', 'Eyeliner'),
        ('mascara', 'Mascara'),
        ('lipstick', 'Lipstick'),
        ('lip_gloss', 'Lip Gloss'),
        ('lip_liner', 'Lip Liner'),
    ]
    
    RANGE_CHOICES = [
        ('korean',    'K-Beauty'),
        ('makeup',    'Makeup'),
        ('treatment', 'Treatment'),
        ('ayurvedic', 'Ayurvedic'),   # NEW
        ('pharmacy',  'Pharmacy'),    # NEW
    ]
    
    SKIN_TYPE_CHOICES = [
        ('oily', 'Oily'),
        ('dry', 'Dry'),
        ('combination', 'Combination'),
        ('normal', 'Normal'),
        ('all', 'All Skin Types'),
    ]
    
    UNDERTONE_CHOICES = [
        ('warm', 'Warm'),
        ('cool', 'Cool'),
        ('neutral', 'Neutral'),
        ('olive', 'Olive'),
    ]
    
    SKIN_TONE_CHOICES = [
        ('fair', 'Fair'),
        ('light', 'Light'),
        ('medium', 'Medium'),
        ('tan', 'Tan'),
        ('deep', 'Deep'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=200)
    brand = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    product_range = models.CharField(max_length=50, choices=RANGE_CHOICES)
    
    # Description and Details
    description = models.TextField(blank=True)
    key_ingredients = models.TextField(blank=True, help_text='Comma-separated list of key ingredients')
    full_ingredients = models.TextField(blank=True)
    
    # Pricing and SKU
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sku = models.CharField(max_length=50, unique=True)
    
    # Image
    image_url = models.URLField(blank=True)
    
    # For Skincare Products
    suitable_for_skin_types = models.JSONField(default=list, blank=True)
    targets = models.JSONField(default=list, blank=True, help_text='List of concern slugs this product addresses')
    
    # For Makeup Products
    shades_available = models.JSONField(default=list, blank=True, help_text='List of shade objects with name and hex color')
    undertone_match = models.CharField(max_length=20, choices=UNDERTONE_CHOICES, blank=True)
    skin_tone_match = models.CharField(max_length=20, choices=SKIN_TONE_CHOICES, blank=True)
    coverage = models.CharField(max_length=50, blank=True)
    finish = models.CharField(max_length=50, blank=True)
    
    # Meta
    is_featured = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['brand', 'name']
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
    
    def __str__(self):
        return f"{self.brand} - {self.name}"
    
    def get_key_ingredients_list(self):
        """Return key ingredients as a list"""
        if self.key_ingredients:
            return [ing.strip() for ing in self.key_ingredients.split(',')]
        return []
    
    def get_price_display(self):
        """Return formatted price"""
        if self.price:
            return f"₹{self.price:,.2f}"
        return "Price on request"