<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class ReferralLog extends Model
{
    public $timestamps = false;

    protected $fillable = [
        'referrer_profile_id', 'referred_profile_id',
        'points_awarded', 'status', 'created_at',
    ];

    protected function casts(): array
    {
        return ['created_at' => 'datetime'];
    }

    public function referrer(): BelongsTo
    {
        return $this->belongsTo(UserProfile::class, 'referrer_profile_id');
    }

    public function referred(): BelongsTo
    {
        return $this->belongsTo(UserProfile::class, 'referred_profile_id');
    }
}
