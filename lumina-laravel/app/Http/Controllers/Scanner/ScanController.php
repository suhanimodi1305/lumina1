<?php

namespace App\Http\Controllers\Scanner;

use App\Exceptions\AiServiceException;
use App\Http\Controllers\Controller;
use App\Http\Requests\Scanner\ScanUploadRequest;
use App\Models\ScanResult;
use App\Services\RewardsService;
use App\Services\ScanService;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\View\View;

class ScanController extends Controller
{
    public function __construct(
        private ScanService    $scanService,
        private RewardsService $rewardsService,
    ) {}

    public function upload(Request $request): View
    {
        return view('scanner.upload', [
            'demoProfiles' => config('lumina.demo_profiles'),
        ]);
    }

    public function process(ScanUploadRequest $request): RedirectResponse
    {
        // Ensure session exists
        if (!$request->session()->has('_token')) {
            $request->session()->regenerate();
        }

        try {
            $scan = $this->scanService->processUpload(
                $request->file('scan_image'),
                $request->user(),
                $request->input('gender', 'female'),
                $request->session()->getId(),
            );

            $request->session()->put('latest_scan_id', $scan->id);

            // Award points for scan
            if ($request->user()) {
                $this->rewardsService->award($request->user(), 'scan', $scan->id);
            }

            return redirect()->route('results.show', $scan)
                ->with('success', 'Your skin analysis is complete!');

        } catch (AiServiceException $e) {
            return back()->with('error', $e->getMessage());
        } catch (\Throwable $e) {
            return back()->with('error', 'Analysis failed. Please try again with a clear, well-lit photo facing the camera.');
        }
    }

    public function demo(Request $request): RedirectResponse
    {
        $profileKey = $request->query('profile', 'combination_warm');
        $gender     = $request->query('gender', 'female');

        if (!in_array($profileKey, config('lumina.demo_profiles'), true)) {
            $profileKey = 'combination_warm';
        }

        if (!$request->session()->has('_token')) {
            $request->session()->regenerate();
        }

        $scan = $this->scanService->createDemo(
            $profileKey,
            in_array($gender, ['male', 'female', 'other'], true) ? $gender : 'female',
            $request->user(),
            $request->session()->getId(),
        );

        $request->session()->put('latest_scan_id', $scan->id);

        return redirect()->route('results.show', $scan);
    }

    public function results(Request $request, ScanResult $scanResult): View
    {
        // Allow owner or same-session access
        $canView = ($scanResult->user_id && $request->user()?->id === $scanResult->user_id)
            || $scanResult->session_key === $request->session()->getId()
            || $scanResult->is_demo;

        abort_unless($canView, 403);

        $scanResult->load('detectedConcerns');

        // Recommended products based on scan
        $recommendedProducts = \App\Models\Product::with('brand')
            ->whereHas('skinConcerns', fn ($q) =>
                $q->whereIn('slug', $scanResult->detectedConcerns->pluck('slug'))
            )
            ->where('skin_tone_match', $scanResult->skin_tone)
            ->inStock()
            ->limit(6)
            ->get();

        return view('scanner.results', compact('scanResult', 'recommendedProducts'));
    }
}
