<?php

namespace App\Services;

use App\Models\LoyaltyPointsLog;
use App\Models\LoyaltyRedemption;
use App\Models\User;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\DB;

class RewardsService
{
    /**
     * Award points to a user for a given action.
     * Returns the number of points awarded.
     */
    public function award(User $user, string $action, ?int $referenceId = null): int
    {
        $points = config("lumina.points.{$action}", 0);

        if ($points <= 0) {
            return 0;
        }

        DB::transaction(function () use ($user, $action, $points, $referenceId): void {
            LoyaltyPointsLog::create([
                'user_id'      => $user->id,
                'action'       => $action,
                'points_earned' => $points,
                'description'  => ucfirst(str_replace('_', ' ', $action)),
                'reference_id' => $referenceId,
                'created_at'   => now(),
            ]);

            $user->profile()->increment('loyalty_points', $points);
        });

        Cache::forget("user.{$user->id}.points");

        return $points;
    }

    /**
     * Award purchase points: 1 point per ₹100 spent.
     */
    public function awardPurchasePoints(User $user, float $amountSpent, int $orderId): int
    {
        $rate   = config('lumina.points.purchase_rate', 1);
        $points = (int) floor($amountSpent / 100) * $rate;

        if ($points <= 0) {
            return 0;
        }

        DB::transaction(function () use ($user, $points, $orderId): void {
            LoyaltyPointsLog::create([
                'user_id'      => $user->id,
                'action'       => 'purchase',
                'points_earned' => $points,
                'description'  => "Purchase reward (₹" . number_format($orderId) . ")",
                'reference_id' => $orderId,
                'created_at'   => now(),
            ]);

            $user->profile()->increment('loyalty_points', $points);
        });

        Cache::forget("user.{$user->id}.points");

        return $points;
    }

    /**
     * Redeem points for a reward.
     */
    public function redeem(User $user, string $rewardType, int $points): LoyaltyRedemption
    {
        $balance = $this->getBalance($user);

        if ($balance < $points) {
            throw new \RuntimeException("Insufficient points. Balance: {$balance}, Required: {$points}");
        }

        return DB::transaction(function () use ($user, $rewardType, $points): LoyaltyRedemption {
            $redemption = LoyaltyRedemption::create([
                'user_id'      => $user->id,
                'points_spent' => $points,
                'reward_type'  => $rewardType,
                'reward_value' => $this->calculateRewardValue($rewardType, $points),
                'status'       => 'pending',
                'created_at'   => now(),
            ]);

            $user->profile()->decrement('loyalty_points', $points);
            Cache::forget("user.{$user->id}.points");

            return $redemption;
        });
    }

    /**
     * Get the current points balance for a user.
     */
    public function getBalance(User $user): int
    {
        return Cache::remember(
            "user.{$user->id}.points",
            300,
            fn () => (int) ($user->profile?->loyalty_points ?? 0)
        );
    }

    /**
     * Check if the user already earned daily login points today.
     */
    public function hasEarnedTodayLogin(User $user): bool
    {
        return LoyaltyPointsLog::where('user_id', $user->id)
            ->where('action', 'login')
            ->whereDate('created_at', today())
            ->exists();
    }

    private function calculateRewardValue(string $rewardType, int $points): float
    {
        // 500 points → ₹50 coupon, etc.
        return match ($rewardType) {
            'coupon'   => round($points / 10, 2),
            'discount' => round($points / 10, 2),
            default    => 0.0,
        };
    }
}
