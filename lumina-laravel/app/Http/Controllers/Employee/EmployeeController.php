<?php

namespace App\Http\Controllers\Employee;

use App\Http\Controllers\Controller;
use App\Models\UserRequirement;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\View\View;

class EmployeeController extends Controller
{
    public function dashboard(Request $request): View
    {
        $stats = [
            'pending'    => UserRequirement::where('assigned_to', $request->user()->id)->where('status', 'pending')->count(),
            'processing' => UserRequirement::where('assigned_to', $request->user()->id)->where('status', 'processing')->count(),
            'completed'  => UserRequirement::where('assigned_to', $request->user()->id)->where('status', 'delivered')->count(),
        ];

        $recent = UserRequirement::where('assigned_to', $request->user()->id)
            ->with('user')
            ->latest()
            ->limit(5)
            ->get();

        return view('employee.dashboard', compact('stats', 'recent'));
    }

    public function requirements(Request $request): View
    {
        $requirements = UserRequirement::where('assigned_to', $request->user()->id)
            ->with(['user', 'products'])
            ->latest()
            ->paginate(15);

        return view('employee.requirements', compact('requirements'));
    }

    public function updateStatus(Request $request, UserRequirement $requirement): RedirectResponse
    {
        abort_unless($requirement->assigned_to === $request->user()->id || $request->user()->hasRole('admin'), 403);

        $request->validate([
            'status'         => 'required|in:pending,accepted,processing,dispatched,delivered,rejected,cancelled',
            'employee_notes' => 'nullable|string|max:1000',
        ]);

        $requirement->update([
            'status'         => $request->input('status'),
            'employee_notes' => $request->input('employee_notes', $requirement->employee_notes),
        ]);

        return back()->with('success', 'Status updated.');
    }
}
