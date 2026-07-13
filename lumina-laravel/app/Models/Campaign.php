<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Campaign extends Model
{
    protected $fillable = [
        'name', 'type', 'status', 'starts_at', 'ends_at',
        'budget', 'spent', 'impressions', 'clicks', 'conversions',
        'revenue', 'created_by',
    ];

    protected function casts(): array
    {
        return [
            'starts_at'   => 'datetime',
            'ends_at'     => 'datetime',
            'budget'      => 'decimal:2',
            'spent'       => 'decimal:2',
            'revenue'     => 'decimal:2',
        ];
    }

    public function creator(): BelongsTo
    {
        return $this->belongsTo(User::class, 'created_by');
    }

    public function banners(): HasMany
    {
        return $this->hasMany(Banner::class);
    }

    public function coupons(): HasMany
    {
        return $this->hasMany(Coupon::class);
    }
}
