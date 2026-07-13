<?php

namespace App\Services;

use App\Models\MembershipPlan;
use App\Models\Subscription;
use App\Models\TierAuditLog;
use App\Models\User;
use App\Models\UserProfile;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\DB;

class MembershipService
{
    /**
     * Get the effective tier for a user, using cache for performance.
     */
    public function getEffectiveTier(User $user): string
    {
        return Cache::remember(
            "user.{$user->id}.tier",
            300,
            fn () => $user->profile?->effective_tier ?? 'normal'
        );
    }

    /**
     * Get the price ceiling (INR) for a given tier.
     * Returns null for VIP (no ceiling).
     */
    public function getPriceCeiling(string $tier): ?int
    {
        return config("lumina.tiers.{$tier}.price_cap");
    }

    /**
     * Apply admin override tier to a profile.
     */
    public function applyAdminOverride(UserProfile $profile, string $tier, User $changedBy): void
    {
        $previous = $profile->effective_tier;

        DB::transaction(function () use ($profile, $tier, $changedBy, $previous): void {
            $profile->update([
                'admin_override_tier'   => $tier,
                'admin_override_active' => true,
            ]);

            TierAuditLog::create([
                'profile_id'     => $profile->id,
                'changed_by'     => $changedBy->id,
                'previous_tier'  => $previous,
                'new_tier'       => $tier,
                'points_deducted' => 0,
                'reason'         => 'admin_override',
            ]);
        });

        Cache::forget("user.{$profile->user_id}.tier");
    }

    /**
     * Subscribe a user to a membership plan.
     */
    public function subscribe(User $user, MembershipPlan $plan): Subscription
    {
        return DB::transaction(function () use ($user, $plan): Subscription {
            // Cancel any active subscription first
            Subscription::where('user_id', $user->id)
                ->where('status', 'active')
                ->update(['status' => 'cancelled']);

            $subscription = Subscription::create([
                'user_id'    => $user->id,
                'plan_id'    => $plan->id,
                'status'     => 'active',
                'starts_at'  => now(),
                'expires_at' => now()->addDays($plan->duration_days),
            ]);

            $previous = $user->profile->effective_tier;

            $user->profile->update([
                'tier'                    => $plan->name,
                'subscription_expires_at' => $subscription->expires_at,
                'tier_updated_at'         => now(),
            ]);

            TierAuditLog::create([
                'profile_id'     => $user->profile->id,
                'changed_by'     => null,
                'previous_tier'  => $previous,
                'new_tier'       => $plan->name,
                'points_deducted' => 0,
                'reason'         => 'subscription',
            ]);

            Cache::forget("user.{$user->id}.tier");

            return $subscription;
        });
    }

    /**
     * Check if a user's subscription has expired and downgrade if needed.
     */
    public function checkExpiry(UserProfile $profile): void
    {
        if ($profile->tier === 'normal') {
            return;
        }

        if ($profile->subscription_expires_at && $profile->subscription_expires_at->isPast()) {
            $previous = $profile->effective_tier;

            $profile->update([
                'tier'            => 'normal',
                'tier_updated_at' => now(),
            ]);

            TierAuditLog::create([
                'profile_id'     => $profile->id,
                'changed_by'     => null,
                'previous_tier'  => $previous,
                'new_tier'       => 'normal',
                'points_deducted' => 0,
                'reason'         => 'subscription_expired',
            ]);

            Cache::forget("user.{$profile->user_id}.tier");
        }
    }
}
