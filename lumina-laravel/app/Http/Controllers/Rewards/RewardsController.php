<?php

namespace App\Http\Controllers\Rewards;

use App\Http\Controllers\Controller;
use App\Models\LoyaltyPointsLog;
use App\Services\RewardsService;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\View\View;

class RewardsController extends Controller
{
    public function __construct(private RewardsService $rewardsService) {}

    public function index(Request $request): View
    {
        $user    = $request->user();
        $balance = $this->rewardsService->getBalance($user);

        $history = LoyaltyPointsLog::where('user_id', $user->id)
            ->latest('created_at')
            ->paginate(20);

        $earnActions = config('lumina.points');

        $redeemOptions = [
            ['type' => 'coupon',   'points' => 500,  'label' => '₹50 Coupon',            'description' => 'Get ₹50 off your next order'],
            ['type' => 'coupon',   'points' => 1000, 'label' => '₹100 Coupon',           'description' => 'Get ₹100 off your next order'],
            ['type' => 'discount', 'points' => 200,  'label' => '₹20 Instant Discount',  'description' => 'Apply to current cart'],
            ['type' => 'scan',     'points' => 300,  'label' => 'Premium AI Analysis',   'description' => 'Unlock advanced skin analysis'],
        ];

        return view('rewards.index', compact('balance', 'history', 'earnActions', 'redeemOptions'));
    }

    public function redeem(Request $request): RedirectResponse
    {
        $request->validate([
            'reward_type' => 'required|in:coupon,discount,scan',
            'points'      => 'required|integer|min:1',
        ]);

        try {
            $redemption = $this->rewardsService->redeem(
                $request->user(),
                $request->input('reward_type'),
                (int) $request->input('points')
            );

            return back()->with('success', 'Reward redeemed successfully!');
        } catch (\RuntimeException $e) {
            return back()->with('error', $e->getMessage());
        }
    }
}
