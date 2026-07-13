<?php

namespace App\Http\Controllers\Dashboard;

use App\Http\Controllers\Controller;
use App\Services\MembershipService;
use App\Services\RewardsService;
use Illuminate\Http\Request;
use Illuminate\View\View;

class DashboardController extends Controller
{
    public function __construct(
        private MembershipService $membershipService,
        private RewardsService    $rewardsService,
    ) {}

    public function home(Request $request): View
    {
        $user   = $request->user()->load('profile');
        $tier   = $this->membershipService->getEffectiveTier($user);
        $points = $this->rewardsService->getBalance($user);

        $latestScan = $user->scanResults()->latest()->with('detectedConcerns')->first();

        $recentOrders = $user->orders()->latest()->limit(3)->get();

        $upcomingAppointment = $user->appointments()
            ->where('status', 'confirmed')
            ->whereDate('appointment_date', '>=', today())
            ->with('doctor.user')
            ->first();

        return view('dashboard.home', compact(
            'user', 'tier', 'points',
            'latestScan', 'recentOrders', 'upcomingAppointment'
        ));
    }

    public function scans(Request $request): View
    {
        $scans = $request->user()->scanResults()
            ->with('detectedConcerns')
            ->latest()
            ->paginate(10);

        return view('dashboard.scans', compact('scans'));
    }

    public function orders(Request $request): View
    {
        $orders = $request->user()->orders()
            ->with('items')
            ->latest()
            ->paginate(10);

        return view('dashboard.orders', compact('orders'));
    }

    public function profile(Request $request): View
    {
        $user = $request->user()->load('profile');
        return view('dashboard.profile', compact('user'));
    }

    public function updateProfile(Request $request): \Illuminate\Http\RedirectResponse
    {
        $validated = $request->validate([
            'name'          => 'required|string|max:150',
            'phone'         => 'nullable|string|max:20',
            'date_of_birth' => 'nullable|date|before:today',
            'gender'        => 'nullable|in:male,female,other',
        ]);

        $request->user()->update(['name' => $validated['name']]);
        $request->user()->profile->update([
            'phone'         => $validated['phone'] ?? null,
            'date_of_birth' => $validated['date_of_birth'] ?? null,
            'gender'        => $validated['gender'] ?? null,
        ]);

        // Award profile completion points if first time
        if ($request->user()->profile->loyalty_points === 0) {
            app(\App\Services\RewardsService::class)->award($request->user(), 'profile');
        }

        return back()->with('success', 'Profile updated.');
    }
}
