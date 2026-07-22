"""
Products app — Django admin registration.
Registers Product and SkinConcern with useful list views, filters, and search.
"""
from django.contrib import admin
from django.utils.html import format_html
from .models import Product, SkinConcern


@admin.register(SkinConcern)
class SkinConcernAdmin(admin.ModelAdmin):
    list_display  = ('name', 'slug', 'icon', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'slug')
    ordering      = ('name',)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display  = (
        'name', 'brand', 'category', 'product_range',
        'price_display', 'is_featured', 'sku', 'created_at',
    )
    list_filter   = ('product_range', 'category', 'is_featured',
                     'undertone_match', 'skin_tone_match')
    search_fields = ('name', 'brand', 'sku', 'key_ingredients', 'description')
    readonly_fields = ('created_at', 'updated_at')
    ordering      = ('brand', 'name')
    list_per_page = 30

    fieldsets = (
        ('Basic Info', {
            'fields': ('name', 'brand', 'category', 'product_range', 'sku', 'price', 'is_featured')
        }),
        ('Description & Ingredients', {
            'fields': ('description', 'key_ingredients', 'full_ingredients')
        }),
        ('Skincare Properties', {
            'fields': ('suitable_for_skin_types', 'targets'),
            'classes': ('collapse',),
        }),
        ('Makeup Properties', {
            'fields': ('shades_available', 'undertone_match', 'skin_tone_match',
                       'coverage', 'finish'),
            'classes': ('collapse',),
        }),
        ('Media', {
            'fields': ('image_url',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description='Price', ordering='price')
    def price_display(self, obj):
        if obj.price:
            return format_html('<strong>₹{:,.0f}</strong>', obj.price)
        return '—'
