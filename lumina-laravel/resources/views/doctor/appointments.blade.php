@extends('layouts.app')
@section('title', 'My Appointments')

@section('content')
<div class="container py-5">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2 class="fw-bold mb-0">My Appointments</h2>
        <a href="{{ route('doctor.book') }}" class="btn btn-lumina">
            <i class="bi bi-calendar-plus me-2"></i>Book New
        </a>
    </div>

    @if($appointments->isEmpty())
    <div class="text-center py-5">
        <i class="bi bi-calendar-x fs-1 text-muted mb-3 d-block"></i>
        <h5>No appointments yet</h5>
        <p class="text-muted">Book a consultation with one of our specialists.</p>
        <a href="{{ route('doctor.book') }}" class="btn btn-lumina">Book Now</a>
    </div>
    @else
    <div class="row g-4">
        @foreach($appointments as $appt)
        <div class="col-md-6 col-lg-4 fade-in-up">
            <div class="card lumina-card shadow-sm h-100">
                <div class="card-body p-4">
                    <div class="d-flex justify-content-between mb-3">
                        <h6 class="fw-semibold mb-0">Dr. {{ $appt->doctor->user?->name }}</h6>
                        <span class="badge bg-{{ match($appt->status){ 'confirmed'=>'success','pending'=>'warning','cancelled'=>'danger',default=>'secondary' } }}">
                            {{ ucfirst($appt->status) }}
                        </span>
                    </div>
                    <p class="text-muted small mb-1">{{ $appt->doctor->specialisation }}</p>
                    <p class="small mb-3">
                        <i class="bi bi-calendar3 me-1"></i>{{ $appt->appointment_date->format('d M Y') }}
                        at {{ date('h:i A', strtotime($appt->slot_time)) }}
                    </p>
                    <a href="{{ route('doctor.room', $appt) }}" class="btn btn-sm btn-outline-lumina w-100">
                        View Consultation
                    </a>
                </div>
            </div>
        </div>
        @endforeach
    </div>
    <div class="mt-4">{{ $appointments->links() }}</div>
    @endif
</div>
@endsection
