@extends('layouts.app')
@section('title', 'My Scans')

@section('content')
<div class="container py-5">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2 class="fw-bold mb-0">My Skin Scans</h2>
        <a href="{{ route('scan.upload') }}" class="btn btn-lumina">
            <i class="bi bi-camera me-2"></i>New Scan
        </a>
    </div>

    @if($scans->isEmpty())
    <div class="text-center py-5">
        <i class="bi bi-camera fs-1 text-muted mb-3 d-block"></i>
        <h5>No scans yet</h5>
        <p class="text-muted">Upload a photo to get your personalised skin analysis.</p>
        <a href="{{ route('scan.upload') }}" class="btn btn-lumina">Start Free Scan</a>
    </div>
    @else
    <div class="row g-4">
        @foreach($scans as $scan)
        <div class="col-md-6 col-lg-4 fade-in-up">
            <div class="card lumina-card shadow-sm h-100">
                <div class="card-body p-4">
                    <div class="d-flex justify-content-between mb-3">
                        <div>
                            <h6 class="fw-semibold mb-0">
                                {{ $scan->is_demo ? '🎭 Demo' : '📸 Analysis' }}
                                #{{ $scan->id }}
                            </h6>
                            <small class="text-muted">{{ $scan->created_at->format('d M Y') }}</small>
                        </div>
                        <div class="harmony-mini">
                            <span class="fw-bold text-lumina-primary fs-5">{{ $scan->harmony_score }}</span>
                            <span class="text-muted" style="font-size:.7rem;"> /100</span>
                        </div>
                    </div>

                    <div class="d-flex flex-wrap gap-2 mb-3">
                        <span class="badge bg-light text-dark border">{{ ucfirst($scan->skin_tone) }}</span>
                        <span class="badge bg-light text-dark border">{{ ucfirst($scan->undertone) }}</span>
                        <span class="badge bg-light text-dark border">{{ ucfirst($scan->skin_type) }}</span>
                    </div>

                    @if($scan->detectedConcerns->count())
                    <div class="d-flex flex-wrap gap-1 mb-3">
                        @foreach($scan->detectedConcerns->take(3) as $concern)
                        <span class="badge bg-lumina-soft text-dark" style="font-size:.7rem;">{{ $concern->name }}</span>
                        @endforeach
                        @if($scan->detectedConcerns->count() > 3)
                        <span class="badge bg-light text-muted" style="font-size:.7rem;">+{{ $scan->detectedConcerns->count()-3 }} more</span>
                        @endif
                    </div>
                    @endif

                    <a href="{{ route('results.show', $scan) }}" class="btn btn-sm btn-outline-lumina w-100">
                        View Report
                    </a>
                </div>
            </div>
        </div>
        @endforeach
    </div>

    <div class="mt-4">{{ $scans->links() }}</div>
    @endif
</div>
@endsection
