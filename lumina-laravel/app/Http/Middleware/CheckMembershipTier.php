<?php

namespace App\Http\Middleware;

use App\Services\MembershipService;
use Closure;
use Illuminate\Http\Request;
use Symfony\Component\HttpFoundation\Response;

class CheckMembershipTier
{
    public function __construct(private MembershipService $membershipService) {}

    /**
     * Usage: Route::middleware('tier:vip')
     */
    public function handle(Request $request, Closure $next, string $requiredTier = 'vip'): Response
    {
        $user = $request->user();

        if (!$user) {
            return redirect()->route('login');
        }

        $tierRank = ['normal' => 0, 'medium' => 1, 'vip' => 2];
        $userTier = $this->membershipService->getEffectiveTier($user);

        if (($tierRank[$userTier] ?? 0) < ($tierRank[$requiredTier] ?? 0)) {
            return redirect()->route('memberships.index')
                ->with('info', "This feature requires {$requiredTier} membership.");
        }

        return $next($request);
    }
}
