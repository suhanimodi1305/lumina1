<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\BelongsToMany;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Database\Eloquent\Builder;

class Product extends Model
{
    protected $fillable = [
        'brand_id',
        'category_id',
        'subcategory_id',
        'name',
        'slug',
        'sku',
        'product_range',
        'description',
        'key_ingredients',
        'full_ingredients',
        'price',
        'offer_price',
        'affiliate_link',
        'suitable_for_skin_types',
        'targets',
        'shades_available',
        'undertone_match',
        'skin_tone_match',
        'coverage',
        'finish',
        'image_url',
        'rating',
        'reviews_count',
        'availability',
        'ai_recommendation_score',
        'external_id',
        'is_featured',
    ];

    protected function casts(): array
    {
        return [
            'suitable_for_skin_types'  => 'array',
            'targets'                  => 'array',
            'shades_available'         => 'array',
            'price'                    => 'decimal:2',
            'offer_price'              => 'decimal:2',
            'rating'                   => 'decimal:2',
            'is_featured'              => 'boolean',
            'ai_recommendation_score'  => 'integer',
            'reviews_count'            => 'integer',
        ];
    }

    // ── Relationships ─────────────────────────────────────────────────────

    public function brand(): BelongsTo
    {
        return $this->belongsTo(Brand::class);
    }

    public function category(): BelongsTo
    {
        return $this->belongsTo(Category::class);
    }

    public function subcategory(): BelongsTo
    {
        return $this->belongsTo(Subcategory::class);
    }

    public function skinConcerns(): BelongsToMany
    {
        return $this->belongsToMany(SkinConcern::class, 'product_skin_concerns');
    }

    public function reviews(): HasMany
    {
        return $this->hasMany(ProductReview::class);
    }

    // ── Scopes ────────────────────────────────────────────────────────────

    public function scopeWithinPriceCap(Builder $query, ?int $cap): Builder
    {
        if ($cap === null) {
            return $query;
        }

        return $query->where(function (Builder $q) use ($cap): void {
            $q->whereNotNull('price')->where('price', '<=', $cap);
        });
    }

    public function scopeFeatured(Builder $query): Builder
    {
        return $query->where('is_featured', true);
    }

    public function scopeInStock(Builder $query): Builder
    {
        return $query->where('availability', 'in_stock');
    }

    // ── Accessors ─────────────────────────────────────────────────────────

    public function getEffectivePriceAttribute(): ?float
    {
        return $this->offer_price ?? $this->price;
    }

    public function getPriceDisplayAttribute(): string
    {
        $price = $this->effective_price;

        return $price ? '₹' . number_format((float) $price, 2) : 'Price on request';
    }

    public function getKeyIngredientsListAttribute(): array
    {
        if (!$this->key_ingredients) {
            return [];
        }

        return array_map('trim', explode(',', $this->key_ingredients));
    }
}
