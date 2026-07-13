<?php

namespace App\Http\Controllers\Auth;

use App\Http\Controllers\Controller;
use App\Models\User;
use App\Models\UserProfile;
use App\Models\ReferralLog;
use Illuminate\Auth\Events\Registered;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Illuminate\Support\Facades\Hash;
use Illuminate\Validation\Rules;
use Illuminate\View\View;

class RegisteredUserController extends Controller
{
    public function create(): View
    {
        return view('auth.register');
    }

    public function store(Request $request): RedirectResponse
    {
        $request->validate([
            'name'          => ['required', 'string', 'max:255'],
            'email'         => ['required', 'string', 'email', 'max:255', 'unique:users'],
            'password'      => ['required', 'confirmed', Rules\Password::defaults()],
            'referral_code' => ['nullable', 'string', 'max:12'],
        ]);

        $user = User::create([
            'name'     => $request->name,
            'email'    => $request->email,
            'password' => Hash::make($request->password),
        ]);

        // Create user profile
        $newProfile = UserProfile::create(['user_id' => $user->id]);

        // Handle referral
        if ($request->filled('referral_code')) {
            try {
                $referrerProfile = UserProfile::where('referral_code', $request->referral_code)
                    ->where('user_id', '!=', $user->id)
                    ->first();

                if ($referrerProfile) {
                    ReferralLog::firstOrCreate([
                        'referrer_id'      => $referrerProfile->id,
                        'referred_user_id' => $newProfile->id,
                    ], [
                        'status'         => 'pending',
                        'points_awarded' => 100,
                    ]);
                }
            } catch (\Throwable) {
                // Never block registration
            }
        }

        event(new Registered($user));
        Auth::login($user);

        return redirect()->route('dashboard');
    }
}
