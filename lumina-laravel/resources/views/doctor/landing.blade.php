@extends('layouts.app')
@section('title', 'Doctor Consultation')

@section('content')
<div class="container py-5">

    {{-- Hero --}}
    <div class="text-center mb-5 fade-in-up">
        <span class="hero-badge mb-3 d-inline-block">👩‍⚕️ Expert Consultation</span>
        <h1 class="fw-bold mb-2">Talk to a Skin Doctor</h1>
        <p class="text-muted fs-5">Get personalised advice from certified dermatologists — powered by your AI scan results.</p>
        @auth
        <a href="{{ route('doctor.book') }}" class="btn btn-lumina btn-lg mt-3">
            <i class="bi bi-calendar-check me-2"></i>Book Appointment
        </a>
        @else
        <a href="{{ route('register') }}" class="btn btn-lumina btn-lg mt-3">Sign Up to Book</a>
        @endauth
    </div>

    {{-- Scan summary if available --}}
    @if($latestScan)
    <div class="row justify-content-center mb-5">
        <div class="col-lg-8">
            <div class="card lumina-card shadow-sm border-primary fade-in-up">
                <div class="card-body p-4">
                    <div class="d-flex justify-content-between align-items-start flex-wrap gap-3">
                        <div>
                            <h5 class="fw-semibold mb-1">Your Latest Scan Results</h5>
                            <p class="text-muted small mb-3">Share these with a doctor for a targeted consultation.</p>
                            <div class="d-flex flex-wrap gap-2">
                                <span class="badge bg-light text-dark border">{{ ucfirst($latestScan->skin_type) }} Skin</span>
                                <span class="badge bg-light text-dark border">{{ ucfirst($latestScan->undertone) }} Undertone</span>
                                <span class="badge bg-light text-dark border">Acne: {{ ucfirst($latestScan->hf_acne_severity) }}</span>
                                @foreach($latestScan->detectedConcerns->take(3) as $concern)
                                <span class="badge bg-lumina-soft text-dark">{{ $concern->name }}</span>
                                @endforeach
                            </div>
                        </div>
                        <a href="{{ route('doctor.book', ['scan_id'=>$latestScan->id]) }}" class="btn btn-outline-lumina">
                            Book with This Scan
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </div>
    @endif

    {{-- Doctors --}}
    <h3 class="fw-bold mb-4">Our Specialists</h3>
    @if($doctors->isEmpty())
    <div class="text-center py-5 text-muted">
        <i class="bi bi-person-x fs-1 mb-3 d-block"></i>
        <p>No doctors available at this time. Please check back soon.</p>
    </div>
    @else
    <div class="row g-4">
        @foreach($doctors as $doctor)
        <div class="col-md-6 col-lg-4 fade-in-up">
            <div class="card lumina-card shadow-sm h-100">
                <div class="card-body p-4 text-center">
                    <div class="doctor-avatar mb-3">
                        <div class="bg-lumina-soft rounded-circle d-inline-flex align-items-center justify-content-center"
                             style="width:72px;height:72px;font-size:1.8rem;">
                            👩‍⚕️
                        </div>
                    </div>
                    <h5 class="fw-bold mb-1">Dr. {{ $doctor->user?->name }}</h5>
                    <p class="text-lumina-primary small fw-semibold mb-1">{{ $doctor->specialisation }}</p>
                    <p class="text-muted small mb-1">{{ $doctor->qualification }}</p>
                    <p class="text-muted small mb-3">{{ $doctor->experience_years }} years experience</p>

                    @if($doctor->languages)
                    <div class="d-flex flex-wrap gap-1 justify-content-center mb-3">
                        @foreach(explode(',', $doctor->languages) as $lang)
                        <span class="badge bg-light text-dark border" style="font-size:.7rem;">{{ trim($lang) }}</span>
                        @endforeach
                    </div>
                    @endif

                    <div class="d-flex gap-2 justify-content-center">
                        <span class="fw-bold text-lumina-primary">₹{{ number_format($doctor->consultation_fee, 0) }}</span>
                        <span class="text-muted small">/session</span>
                    </div>
                </div>
                <div class="card-footer bg-transparent p-3 border-top-0">
                    @auth
                    <a href="{{ route('doctor.book', ['doctor_id'=>$doctor->id]) }}" class="btn btn-lumina btn-sm w-100">
                        Book Consultation
                    </a>
                    @else
                    <a href="{{ route('login') }}" class="btn btn-outline-lumina btn-sm w-100">Login to Book</a>
                    @endauth
                </div>
            </div>
        </div>
        @endforeach
    </div>
    @endif
</div>
@endsection
