<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\RateLimiter;
use Symfony\Component\HttpFoundation\Response;

class ThrottleScanUploads
{
    public function handle(Request $request, Closure $next): Response
    {
        $key = 'scan:' . ($request->user()?->id ?? $request->ip());

        if (RateLimiter::tooManyAttempts($key, 10)) {
            $seconds = RateLimiter::availableIn($key);

            return response()->json([
                'error' => "Too many scan uploads. Try again in {$seconds} seconds.",
            ], 429);
        }

        RateLimiter::hit($key, 3600); // 10 per hour

        return $next($request);
    }
}
