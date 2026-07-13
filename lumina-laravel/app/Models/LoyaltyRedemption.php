<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class LoyaltyRedemption extends Model
{
    public $timestamps = false;

    protected $fillable = [
        'user_id', 'points_spent', 'reward_type',
        'reward_value', 'coupon_id', 'status', 'created_at',
    ];

    protected function casts(): array
    {
        return [
            'reward_value' => 'decimal:2',
            'created_at'   => 'datetime',
        ];
    }

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    public function coupon(): BelongsTo
    {
        return $this->belongsTo(Coupon::class);
    }
}
