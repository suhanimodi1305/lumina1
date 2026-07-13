<?php

namespace App\Http\Controllers\Marketing;

use App\Http\Controllers\Controller;
use App\Models\Banner;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\View\View;

class BannerController extends Controller
{
    public function index(): View
    {
        $banners = Banner::orderBy('sort_order')->paginate(15);
        return view('marketing.banners.index', compact('banners'));
    }

    public function create(): View
    {
        return view('marketing.banners.form', ['banner' => null]);
    }

    public function store(Request $request): RedirectResponse
    {
        $validated = $request->validate([
            'title'      => 'required|string|max:150',
            'placement'  => 'required|string|max:100',
            'image_url'  => 'nullable|url',
            'link_url'   => 'nullable|url',
            'sort_order' => 'integer|min:0',
            'is_active'  => 'boolean',
        ]);

        Banner::create($validated);

        return redirect()->route('marketing.banners.index')->with('success', 'Banner created.');
    }

    public function edit(Banner $banner): View
    {
        return view('marketing.banners.form', compact('banner'));
    }

    public function update(Request $request, Banner $banner): RedirectResponse
    {
        $validated = $request->validate([
            'title'      => 'required|string|max:150',
            'placement'  => 'required|string|max:100',
            'image_url'  => 'nullable|url',
            'link_url'   => 'nullable|url',
            'sort_order' => 'integer|min:0',
            'is_active'  => 'boolean',
        ]);

        $banner->update($validated);

        return redirect()->route('marketing.banners.index')->with('success', 'Banner updated.');
    }

    public function destroy(Banner $banner): RedirectResponse
    {
        $banner->delete();
        return redirect()->route('marketing.banners.index')->with('success', 'Banner deleted.');
    }
}
