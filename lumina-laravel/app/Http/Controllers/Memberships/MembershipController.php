<?php

namespace App\Http\Controllers\Memberships;

use App\Http\Controllers\Controller;
use App\Models\MembershipPlan;
use App\Services\MembershipService;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\View\View;

class MembershipController extends Controller
{
    public function __construct(private MembershipService $membershipService) {}

    public function index(Request $request): View
    {
        $plans       = MembershipPlan::where('is_active', true)->orderBy('price')->get();
        $currentTier = $this->membershipService->getEffectiveTier($request->user());

        return view('memberships.index', compact('plans', 'currentTier'));
    }

    public function subscribe(Request $request): RedirectResponse
    {
        $request->validate(['plan_id' => 'required|exists:membership_plans,id']);

        $plan = MembershipPlan::findOrFail($request->input('plan_id'));

        if (!$plan->is_active) {
            return back()->with('error', 'This plan is no longer available.');
        }

        $subscription = $this->membershipService->subscribe($request->user(), $plan);

        return redirect()->route('dashboard')
            ->with('success', "Welcome to {$plan->display_name} membership!");
    }
}
