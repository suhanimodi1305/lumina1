<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Support\Str;

class UserProfile extends Model
{
    protected $fillable = [
        'user_id',
        'tier',
        'referral_code',
        'loyalty_points',
        'tier_updated_at',
        'subscription_expires_at',
        'staff_role',
        'admin_override_tier',
        'admin_override_active',
        'avatar',
        'phone',
        'date_of_birth',
        'gender',
    ];

    protected function casts(): array
    {
        return [
            'tier_updated_at'         => 'datetime',
            'subscription_expires_at' => 'datetime',
            'admin_override_active'   => 'boolean',
            'date_of_birth'           => 'date',
        ];
    }

    // ── Boot ─────────────────────────────────────────────────────────────

    protected static function booted(): void
    {
        static::creating(function (UserProfile $profile): void {
            if (empty($profile->referral_code)) {
                $profile->referral_code = static::generateReferralCode();
            }
        });
    }

    // ── Relationships ─────────────────────────────────────────────────────

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    public function referralsMade(): HasMany
    {
        return $this->hasMany(ReferralLog::class, 'referrer_profile_id');
    }

    public function tierAuditLogs(): HasMany
    {
        return $this->hasMany(TierAuditLog::class, 'profile_id');
    }

    // ── Accessors ─────────────────────────────────────────────────────────

    /**
     * Returns the tier that should actually be enforced.
     * Admin override wins over subscription tier.
     */
    public function getEffectiveTierAttribute(): string
    {
        if ($this->admin_override_active && $this->admin_override_tier) {
            return $this->admin_override_tier;
        }

        return $this->tier ?? 'normal';
    }

    // ── Helpers ───────────────────────────────────────────────────────────

    public static function generateReferralCode(): string
    {
        $length = config('lumina.referral_code_length', 10);

        do {
            $code = strtoupper(Str::random($length));
        } while (static::where('referral_code', $code)->exists());

        return $code;
    }
}
