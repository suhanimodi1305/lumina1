<?php

namespace App\Http\Controllers\Doctor;

use App\Http\Controllers\Controller;
use App\Models\DoctorProfile;
use Illuminate\Http\Request;
use Illuminate\View\View;

class DoctorController extends Controller
{
    public function landing(Request $request): View
    {
        $doctors = DoctorProfile::with('user')
            ->where('is_active', true)
            ->get();

        $latestScan = null;
        if ($request->user()) {
            $latestScan = $request->user()->scanResults()->latest()->with('detectedConcerns')->first();
        }

        return view('doctor.landing', compact('doctors', 'latestScan'));
    }
}
