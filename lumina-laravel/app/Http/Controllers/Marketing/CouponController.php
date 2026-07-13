<?php

namespace App\Http\Controllers\Marketing;

use App\Http\Controllers\Controller;
use App\Models\Coupon;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\View\View;

class CouponController extends Controller
{
    public function index(): View
    {
        $coupons = Coupon::latest()->paginate(15);
        return view('marketing.coupons.index', compact('coupons'));
    }

    public function create(): View
    {
        return view('marketing.coupons.form', ['coupon' => null]);
    }

    public function store(Request $request): RedirectResponse
    {
        $validated = $request->validate([
            'code'           => 'required|string|max:30|unique:coupons,code',
            'discount_type'  => 'required|in:flat,percent',
            'discount_value' => 'required|numeric|min:1',
            'min_order'      => 'nullable|numeric|min:0',
            'max_discount'   => 'nullable|numeric|min:0',
            'usage_limit'    => 'nullable|integer|min:1',
            'expires_at'     => 'nullable|date',
            'is_active'      => 'boolean',
        ]);

        Coupon::create($validated);

        return redirect()->route('marketing.coupons.index')->with('success', 'Coupon created.');
    }

    public function edit(Coupon $coupon): View
    {
        return view('marketing.coupons.form', compact('coupon'));
    }

    public function update(Request $request, Coupon $coupon): RedirectResponse
    {
        $validated = $request->validate([
            'code'           => 'required|string|max:30|unique:coupons,code,' . $coupon->id,
            'discount_type'  => 'required|in:flat,percent',
            'discount_value' => 'required|numeric|min:1',
            'min_order'      => 'nullable|numeric|min:0',
            'max_discount'   => 'nullable|numeric|min:0',
            'usage_limit'    => 'nullable|integer|min:1',
            'expires_at'     => 'nullable|date',
            'is_active'      => 'boolean',
        ]);

        $coupon->update($validated);

        return redirect()->route('marketing.coupons.index')->with('success', 'Coupon updated.');
    }

    public function destroy(Coupon $coupon): RedirectResponse
    {
        $coupon->delete();
        return redirect()->route('marketing.coupons.index')->with('success', 'Coupon deleted.');
    }
}
