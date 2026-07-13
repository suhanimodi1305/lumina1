@extends('layouts.app')
@section('title', 'My Dashboard')

@section('content')
<div class="container py-4">

    {{-- Welcome banner --}}
    <div class="welcome-banner mb-4 fade-in-up">
        <div class="row align-items-center">
            <div class="col">
                <h2 class="fw-bold mb-1">Hello, {{ $user->name }} 👋</h2>
                <p class="text-muted mb-0">
                    <span class="tier-badge tier-{{ $tier }} me-2">{{ strtoupper($tier) }}</span>
                    ✨ {{ number_format($points) }} points
                </p>
            </div>
            <div class="col-auto">
                <a href="{{ route('scan.upload') }}" class="btn btn-lumina">
                    <i class="bi bi-camera me-2"></i>New Scan
                </a>
            </div>
        </div>
    </div>

    <div class="row g-4">

        {{-- Latest scan summary --}}
        <div class="col-lg-5">
            @if($latestScan)
            <div class="card lumina-card shadow-sm h-100 fade-in-up">
                <div class="card-body p-4">
                    <div class="d-flex justify-content-between align-items-start mb-3">
                        <h5 class="fw-semibold mb-0">Latest Skin Scan</h5>
                        <small class="text-muted">{{ $latestScan->created_at->diffForHumans() }}</small>
                    </div>
                    <div class="row g-3 mb-3">
                        @foreach([
                            ['label'=>'Harmony','score'=>$latestScan->harmony_score,'color'=>'#c9a84c'],
                            ['label'=>'Hydration','score'=>$latestScan->hydration_score,'color'=>'#4a90d9'],
                            ['label'=>'Acne-Free','score'=>100-$latestScan->acne_score,'color'=>'#e74c3c'],
                        ] as $s)
                        <div class="col-4 text-center">
                            <div class="fw-bold fs-4" style="color:{{ $s['color'] }}" data-count="{{ $s['score'] }}">{{ $s['score'] }}</div>
                            <div class="text-muted small">{{ $s['label'] }}</div>
                        </div>
                        @endforeach
                    </div>
                    <div class="d-flex flex-wrap gap-2 mb-3">
                        <span class="badge bg-light text-dark border">{{ ucfirst($latestScan->skin_tone) }} Tone</span>
                        <span class="badge bg-light text-dark border">{{ ucfirst($latestScan->undertone) }}</span>
                        <span class="badge bg-light text-dark border">{{ ucfirst($latestScan->skin_type) }}</span>
                    </div>
                    <div class="d-flex gap-2">
                        <a href="{{ route('results.show', $latestScan) }}" class="btn btn-sm btn-outline-lumina">View Report</a>
                        <a href="{{ route('chat.create', ['mode'=>'doctor','scan_id'=>$latestScan->id]) }}" class="btn btn-sm btn-lumina">Ask AI</a>
                    </div>
                </div>
            </div>
            @else
            <div class="card lumina-card h-100 border-dashed fade-in-up">
                <div class="card-body p-4 text-center d-flex flex-column align-items-center justify-content-center">
                    <i class="bi bi-camera fs-1 text-lumina-primary mb-3"></i>
                    <h5 class="fw-semibold">No Scan Yet</h5>
                    <p class="text-muted small mb-4">Upload a selfie for your personalised skin report</p>
                    <a href="{{ route('scan.upload') }}" class="btn btn-lumina">Start Free Scan</a>
                </div>
            </div>
            @endif
        </div>

        {{-- Quick actions --}}
        <div class="col-lg-7">
            <div class="row g-3">
                @foreach([
                    ['icon'=>'bi-chat-heart','label'=>'AI Doctor','sub'=>'Ask Dr. Lumina','href'=>route('chat.create',['mode'=>'doctor']),'color'=>'#c9a84c'],
                    ['icon'=>'bi-brush','label'=>'Makeup AI','sub'=>'Shade matching','href'=>route('chat.create',['mode'=>'makeup']),'color'=>'#9b7cb8'],
                    ['icon'=>'bi-flower1','label'=>'K-Beauty','sub'=>'Routines','href'=>route('chat.create',['mode'=>'kbeauty']),'color'=>'#e8a87c'],
                    ['icon'=>'bi-clipboard2-pulse','label'=>'Doctor','sub'=>'Book consultation','href'=>route('doctor.book'),'color'=>'#4a90d9'],
                    ['icon'=>'bi-bag-heart','label'=>'Shop','sub'=>'Browse products','href'=>route('products.index'),'color'=>'#27ae60'],
                    ['icon'=>'bi-gift','label'=>'Rewards','sub'=>number_format($points).' pts','href'=>route('rewards.index'),'color'=>'#e74c3c'],
                ] as $action)
                <div class="col-6 col-md-4 fade-in-up">
                    <a href="{{ $action['href'] }}" class="quick-action-card text-decoration-none">
                        <div class="quick-action-icon" style="background:{{ $action['color'] }}20;color:{{ $action['color'] }};">
                            <i class="bi {{ $action['icon'] }} fs-4"></i>
                        </div>
                        <div class="quick-action-label fw-semibold small">{{ $action['label'] }}</div>
                        <div class="quick-action-sub text-muted" style="font-size:.72rem;">{{ $action['sub'] }}</div>
                    </a>
                </div>
                @endforeach
            </div>
        </div>

        {{-- Recent orders --}}
        @if($recentOrders->count())
        <div class="col-lg-6 fade-in-up">
            <div class="card lumina-card shadow-sm">
                <div class="card-body p-4">
                    <div class="d-flex justify-content-between mb-3">
                        <h5 class="fw-semibold mb-0">Recent Orders</h5>
                        <a href="{{ route('dashboard.orders') }}" class="btn btn-sm btn-outline-secondary">View All</a>
                    </div>
                    @foreach($recentOrders as $order)
                    <div class="d-flex justify-content-between align-items-center py-2 border-bottom">
                        <div>
                            <div class="fw-semibold small">{{ $order->order_id }}</div>
                            <div class="text-muted" style="font-size:.75rem;">{{ $order->created_at->format('d M Y') }} · ₹{{ number_format($order->total, 0) }}</div>
                        </div>
                        <span class="badge bg-{{ match($order->status){ 'delivered'=>'success','cancelled'=>'danger','shipped'=>'primary',default=>'warning' } }}">
                            {{ ucwords(str_replace('_',' ',$order->status)) }}
                        </span>
                    </div>
                    @endforeach
                </div>
            </div>
        </div>
        @endif

        {{-- Upcoming appointment --}}
        @if($upcomingAppointment)
        <div class="col-lg-6 fade-in-up">
            <div class="card lumina-card shadow-sm border-primary">
                <div class="card-body p-4">
                    <h5 class="fw-semibold mb-3"><i class="bi bi-calendar-check text-primary me-2"></i>Upcoming Appointment</h5>
                    <p class="mb-1 fw-medium">Dr. {{ $upcomingAppointment->doctor->user->name }}</p>
                    <p class="text-muted small mb-1">{{ $upcomingAppointment->doctor->specialisation }}</p>
                    <p class="mb-3"><i class="bi bi-clock me-1"></i>{{ $upcomingAppointment->appointment_date->format('d M Y') }} at {{ $upcomingAppointment->slot_time }}</p>
                    <a href="{{ route('doctor.room', $upcomingAppointment) }}" class="btn btn-sm btn-lumina">Join Consultation</a>
                </div>
            </div>
        </div>
        @endif

    </div>
</div>

@push('styles')
<style>
.welcome-banner { background:linear-gradient(135deg,#1a1a2e,#2d1b4e);color:#fff;border-radius:16px;padding:1.5rem 2rem; }
.quick-action-card { display:flex;flex-direction:column;align-items:center;justify-content:center;background:#fff;border:1px solid rgba(0,0,0,.07);border-radius:14px;padding:1.2rem;text-align:center;transition:all .25s; }
.quick-action-card:hover { transform:translateY(-4px);box-shadow:0 8px 24px rgba(0,0,0,.1); }
.quick-action-icon { width:52px;height:52px;border-radius:14px;display:flex;align-items:center;justify-content:center;margin-bottom:.6rem; }
</style>
@endpush
@endsection
