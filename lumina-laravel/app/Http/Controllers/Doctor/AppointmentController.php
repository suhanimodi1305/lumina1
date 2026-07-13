<?php

namespace App\Http\Controllers\Doctor;

use App\Http\Controllers\Controller;
use App\Models\Appointment;
use App\Models\AppointmentMessage;
use App\Models\DoctorProfile;
use App\Models\Prescription;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Storage;
use Illuminate\View\View;

class AppointmentController extends Controller
{
    public function index(Request $request): View
    {
        $appointments = $request->user()->appointments()
            ->with('doctor.user')
            ->latest()
            ->paginate(10);

        return view('doctor.appointments', compact('appointments'));
    }

    public function book(Request $request): View
    {
        $doctors    = DoctorProfile::with('user')->where('is_active', true)->get();
        $latestScan = $request->user()->scanResults()->latest()->first();

        return view('doctor.book', compact('doctors', 'latestScan'));
    }

    public function store(Request $request): RedirectResponse
    {
        $validated = $request->validate([
            'doctor_id'        => 'required|exists:doctor_profiles,id',
            'appointment_date' => 'required|date|after:today',
            'slot_time'        => 'required|date_format:H:i',
            'notes'            => 'nullable|string|max:500',
            'scan_result_id'   => 'nullable|exists:scan_results,id',
        ]);

        $appointment = Appointment::create([
            'patient_id'       => $request->user()->id,
            'doctor_id'        => $validated['doctor_id'],
            'scan_result_id'   => $validated['scan_result_id'] ?? null,
            'appointment_date' => $validated['appointment_date'],
            'slot_time'        => $validated['slot_time'],
            'status'           => 'pending',
            'notes'            => $validated['notes'] ?? null,
        ]);

        return redirect()->route('doctor.room', $appointment)
            ->with('success', 'Appointment booked! The doctor will confirm shortly.');
    }

    public function room(Request $request, Appointment $appointment): View
    {
        $canAccess = $appointment->patient_id === $request->user()->id
            || ($request->user()->hasRole('doctor') && $appointment->doctor->user_id === $request->user()->id);

        abort_unless($canAccess, 403);

        $appointment->load(['doctor.user', 'patient', 'messages.sender', 'prescription', 'scanResult']);

        return view('doctor.room', compact('appointment'));
    }

    public function sendMessage(Request $request, Appointment $appointment): JsonResponse
    {
        $canAccess = $appointment->patient_id === $request->user()->id
            || ($request->user()->hasRole('doctor') && $appointment->doctor->user_id === $request->user()->id);

        abort_unless($canAccess, 403);

        $request->validate(['message' => 'required|string|max:1000']);

        $role = $appointment->patient_id === $request->user()->id ? 'patient' : 'doctor';

        $msg = AppointmentMessage::create([
            'appointment_id' => $appointment->id,
            'sender_id'      => $request->user()->id,
            'role'           => $role,
            'message'        => $request->input('message'),
        ]);

        return response()->json([
            'id'         => $msg->id,
            'role'       => $msg->role,
            'message'    => $msg->message,
            'sender'     => $request->user()->name,
            'created_at' => $msg->created_at->format('h:i A'),
        ]);
    }
}
