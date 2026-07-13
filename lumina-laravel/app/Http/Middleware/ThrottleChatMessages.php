<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\RateLimiter;
use Symfony\Component\HttpFoundation\Response;

class ThrottleChatMessages
{
    public function handle(Request $request, Closure $next): Response
    {
        $key = 'chat:' . ($request->user()?->id ?? $request->ip());

        if (RateLimiter::tooManyAttempts($key, 60)) {
            $seconds = RateLimiter::availableIn($key);

            return response()->json([
                'error' => "Too many messages. Try again in {$seconds} seconds.",
            ], 429);
        }

        RateLimiter::hit($key, 3600); // 60 per hour

        return $next($request);
    }
}
