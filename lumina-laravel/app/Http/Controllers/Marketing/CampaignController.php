<?php

namespace App\Http\Controllers\Marketing;

use App\Http\Controllers\Controller;
use App\Models\Campaign;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\View\View;

class CampaignController extends Controller
{
    public function index(): View
    {
        $campaigns = Campaign::with('creator')->latest()->paginate(15);
        return view('marketing.campaigns.index', compact('campaigns'));
    }

    public function create(): View
    {
        return view('marketing.campaigns.form', ['campaign' => null]);
    }

    public function store(Request $request): RedirectResponse
    {
        $validated = $request->validate([
            'name'       => 'required|string|max:150',
            'type'       => 'required|in:email,sms,push,social,banner',
            'status'     => 'required|in:draft,active,paused,ended',
            'start_date' => 'required|date',
            'end_date'   => 'nullable|date|after_or_equal:start_date',
            'content'    => 'nullable|string',
        ]);

        Campaign::create(array_merge($validated, ['created_by' => $request->user()->id]));

        return redirect()->route('marketing.campaigns.index')->with('success', 'Campaign created.');
    }

    public function edit(Campaign $campaign): View
    {
        return view('marketing.campaigns.form', compact('campaign'));
    }

    public function update(Request $request, Campaign $campaign): RedirectResponse
    {
        $validated = $request->validate([
            'name'       => 'required|string|max:150',
            'type'       => 'required|in:email,sms,push,social,banner',
            'status'     => 'required|in:draft,active,paused,ended',
            'start_date' => 'required|date',
            'end_date'   => 'nullable|date|after_or_equal:start_date',
            'content'    => 'nullable|string',
        ]);

        $campaign->update($validated);

        return redirect()->route('marketing.campaigns.index')->with('success', 'Campaign updated.');
    }

    public function destroy(Campaign $campaign): RedirectResponse
    {
        $campaign->delete();
        return redirect()->route('marketing.campaigns.index')->with('success', 'Campaign deleted.');
    }
}
