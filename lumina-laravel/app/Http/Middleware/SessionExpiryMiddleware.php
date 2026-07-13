<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Symfony\Component\HttpFoundation\Response;

class SessionExpiryMiddleware
{
    public function handle(Request $request, Closure $next): Response
    {
        if (Auth::check()) {
            $expiryMinutes = config('lumina.session_expiry_minutes', 120);
            $lastActivity  = session('last_activity_at');

            if ($lastActivity && now()->diffInMinutes($lastActivity) >= $expiryMinutes) {
                Auth::logout();
                $request->session()->invalidate();
                $request->session()->regenerateToken();

                return redirect()->route('login')
                    ->with('status', 'Your session has expired. Please log in again.');
            }

            // Sliding window: refresh on every request
            session(['last_activity_at' => now()]);
        }

        return $next($request);
    }
}
