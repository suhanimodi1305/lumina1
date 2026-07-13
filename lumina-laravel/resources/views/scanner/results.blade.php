@extends('layouts.app')
@section('title', 'Your Skin Analysis Results')

@push('styles')
<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js">
@endpush

@section('content')
<div class="container py-5">

    {{-- Header --}}
    <div class="text-center mb-5 fade-in-up">
        <div class="result-harmony-badge mb-3">
            <div class="harmony-circle" style="--score:{{ $scanResult->harmony_score }}">
                <span class="harmony-value">{{ $scanResult->harmony_score }}</span>
                <span class="harmony-label">Harmony</span>
            </div>
        </div>
        <h1 class="fw-bold">Your Skin Report</h1>
        <p class="text-muted">
            {{ $scanResult->is_demo ? '🎭 Demo Profile' : '📸 Analysed ' . $scanResult->created_at->diffForHumans() }}
        </p>
    </div>

    <div class="row g-4">

        {{-- Left: Key attributes --}}
        <div class="col-lg-4">
            <div class="card lumina-card shadow-sm mb-4 fade-in-up">
                <div class="card-body p-4">
                    <h5 class="fw-semibold mb-4">Skin Profile</h5>
                    @php
                        $attrs = [
                            ['label'=>'Skin Tone',  'value'=> ucfirst($scanResult->skin_tone),  'icon'=>'🌅'],
                            ['label'=>'Undertone',  'value'=> ucfirst($scanResult->undertone),  'icon'=>'🎨'],
                            ['label'=>'Face Shape', 'value'=> ucfirst($scanResult->face_shape), 'icon'=>'💎'],
                            ['label'=>'Skin Type',  'value'=> ucfirst($scanResult->skin_type),  'icon'=>'💧'],
                            ['label'=>'Skin Age',   'value'=> $scanResult->skin_age . ' yrs',  'icon'=>'⏳'],
                            ['label'=>'Acne',       'value'=> ucfirst($scanResult->hf_acne_severity), 'icon'=>'🔴'],
                        ];
                    @endphp
                    @foreach($attrs as $attr)
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <span class="text-muted">{{ $attr['icon'] }} {{ $attr['label'] }}</span>
                        <span class="badge bg-lumina-soft text-dark px-3 py-2 fw-semibold">{{ $attr['value'] }}</span>
                    </div>
                    @endforeach
                </div>
            </div>

            {{-- Detected concerns --}}
            @if($scanResult->detectedConcerns->count())
            <div class="card lumina-card shadow-sm fade-in-up">
                <div class="card-body p-4">
                    <h5 class="fw-semibold mb-3">Detected Concerns</h5>
                    <div class="d-flex flex-wrap gap-2">
                        @foreach($scanResult->detectedConcerns as $concern)
                        <span class="concern-badge">{{ $concern->icon }} {{ $concern->name }}</span>
                        @endforeach
                    </div>
                </div>
            </div>
            @endif
        </div>

        {{-- Middle: Score bars --}}
        <div class="col-lg-4">
            <div class="card lumina-card shadow-sm h-100 fade-in-up">
                <div class="card-body p-4">
                    <h5 class="fw-semibold mb-4">Skin Scores</h5>
                    @php
                        $scores = [
                            ['label'=>'Hydration',    'score'=>$scanResult->hydration_score,    'color'=>'#4a90d9'],
                            ['label'=>'Elasticity',   'score'=>$scanResult->elasticity_score,   'color'=>'#7b68ee'],
                            ['label'=>'Harmony',      'score'=>$scanResult->harmony_score,      'color'=>'#c9a84c'],
                            ['label'=>'Pigmentation', 'score'=>100-$scanResult->pigmentation_score, 'color'=>'#e67e22'],
                            ['label'=>'Acne-Free',    'score'=>100-$scanResult->acne_score,     'color'=>'#e74c3c'],
                            ['label'=>'Anti-Aging',   'score'=>100-$scanResult->aging_score,    'color'=>'#27ae60'],
                        ];
                    @endphp
                    @foreach($scores as $s)
                    <div class="mb-3">
                        <div class="d-flex justify-content-between mb-1">
                            <span class="small fw-medium">{{ $s['label'] }}</span>
                            <span class="small fw-bold">{{ $s['score'] }}/100</span>
                        </div>
                        <div class="progress lumina-progress" style="height:8px;">
                            <div class="progress-bar score-bar"
                                 role="progressbar"
                                 style="width:0%; background:{{ $s['color'] }};"
                                 data-width="{{ $s['score'] }}">
                            </div>
                        </div>
                    </div>
                    @endforeach
                </div>
            </div>
        </div>

        {{-- Right: Facial zones + actions --}}
        <div class="col-lg-4">
            <div class="card lumina-card shadow-sm mb-4 fade-in-up">
                <div class="card-body p-4">
                    <h5 class="fw-semibold mb-3">Facial Zones</h5>
                    @php
                        $zones = $scanResult->facial_zones ?? [];
                        $zoneColors = ['none'=>'success','mild'=>'warning','moderate'=>'orange','severe'=>'danger'];
                    @endphp
                    @if(!empty($zones))
                    @foreach($zones as $zone => $severity)
                    <div class="d-flex justify-content-between align-items-center mb-2">
                        <span class="text-muted small text-capitalize">{{ str_replace('_', ' ', $zone) }}</span>
                        <span class="badge bg-{{ $zoneColors[$severity] ?? 'secondary' }}">{{ ucfirst($severity) }}</span>
                    </div>
                    @endforeach
                    @else
                    <p class="text-muted small">No zone data available.</p>
                    @endif
                </div>
            </div>

            {{-- Action buttons --}}
            <div class="card lumina-card shadow-sm fade-in-up">
                <div class="card-body p-4">
                    <h5 class="fw-semibold mb-3">What's Next?</h5>
                    <div class="d-grid gap-2">
                        <a href="{{ route('chat.create', ['mode'=>'doctor','scan_id'=>$scanResult->id]) }}" class="btn btn-lumina">
                            <i class="bi bi-chat-heart me-2"></i>Talk to Dr. Lumina
                        </a>
                        <a href="{{ route('chat.create', ['mode'=>'makeup','scan_id'=>$scanResult->id]) }}" class="btn btn-outline-lumina">
                            <i class="bi bi-brush me-2"></i>Get Makeup Advice
                        </a>
                        <a href="{{ route('chat.create', ['mode'=>'kbeauty','scan_id'=>$scanResult->id]) }}" class="btn btn-outline-secondary">
                            🌸 K-Beauty Routine
                        </a>
                        <a href="{{ route('doctor.book') }}" class="btn btn-outline-secondary">
                            <i class="bi bi-clipboard2-pulse me-2"></i>Book Doctor
                        </a>
                    </div>
                </div>
            </div>
        </div>
    </div>

    {{-- Product recommendations --}}
    @if($recommendedProducts->count())
    <div class="mt-5 fade-in-up">
        <h3 class="fw-bold mb-4">Recommended For Your Skin</h3>
        <div class="row g-4">
            @foreach($recommendedProducts as $product)
                @include('components.product-card', ['product' => $product])
            @endforeach
        </div>
    </div>
    @endif

</div>
@endsection

@push('scripts')
<script>
// Animate score bars on scroll
const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.querySelectorAll('.score-bar').forEach(bar => {
                const w = bar.dataset.width;
                setTimeout(() => { bar.style.width = w + '%'; bar.style.transition = 'width 1s ease'; }, 100);
            });
        }
    });
}, { threshold: 0.3 });

document.querySelectorAll('.lumina-card').forEach(card => observer.observe(card));
</script>
@endpush
