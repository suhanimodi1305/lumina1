<?php

namespace App\Http\Controllers\Marketing;

use App\Http\Controllers\Controller;
use App\Models\Banner;
use App\Models\Campaign;
use App\Models\Coupon;
use Illuminate\Http\Request;
use Illuminate\View\View;

class MarketingController extends Controller
{
    public function dashboard(Request $request): View
    {
        $stats = [
            'active_campaigns'  => Campaign::where('status', 'active')->count(),
            'active_coupons'    => Coupon::where('is_active', true)->count(),
            'active_banners'    => Banner::where('is_active', true)->count(),
            'total_impressions' => Campaign::sum('impressions'),
            'total_clicks'      => Campaign::sum('clicks'),
            'total_conversions' => Campaign::sum('conversions'),
            'total_revenue'     => Campaign::sum('revenue'),
        ];

        $recentCampaigns = Campaign::with('creator')->latest()->limit(5)->get();
        $activeBanners   = Banner::where('is_active', true)->orderBy('sort_order')->limit(10)->get();

        return view('marketing.dashboard', compact('stats', 'recentCampaigns', 'activeBanners'));
    }
}
