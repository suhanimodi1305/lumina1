@extends('layouts.app')
@section('title', 'Rewards — Log & Earn')

@section('content')
<div class="container py-5">
    <div class="text-center mb-5 fade-in-up">
        <span class="hero-badge mb-3 d-inline-block">🎁 Log & Earn</span>
        <h1 class="fw-bold">Your Rewards</h1>
        <div class="points-balance-badge d-inline-block mt-3 points-pop">
            <span class="display-5 fw-bold text-lumina-primary" data-count="{{ $balance }}">{{ number_format($balance) }}</span>
            <span class="text-muted ms-2">points</span>
        </div>
    </div>

    <div class="row g-4">
        {{-- Earn section --}}
        <div class="col-lg-4 fade-in-up">
            <div class="card lumina-card shadow-sm h-100">
                <div class="card-body p-4">
                    <h5 class="fw-semibold mb-4">Ways to Earn</h5>
                    @foreach([
                        ['action'=>'login',   'label'=>'Daily Login',       'pts'=>$earnActions['login'],          'icon'=>'🌅'],
                        ['action'=>'scan',    'label'=>'AI Skin Analysis',  'pts'=>$earnActions['scan'],           'icon'=>'📸'],
                        ['action'=>'review',  'label'=>'Write a Review',    'pts'=>$earnActions['review'],         'icon'=>'⭐'],
                        ['action'=>'referral','label'=>'Refer a Friend',    'pts'=>$earnActions['referral'],       'icon'=>'👥'],
                        ['action'=>'profile', 'label'=>'Complete Profile',  'pts'=>$earnActions['profile'],        'icon'=>'👤'],
                        ['action'=>'tutorial','label'=>'Watch Tutorial',    'pts'=>$earnActions['tutorial'],       'icon'=>'🎥'],
                        ['action'=>'purchase','label'=>'Purchase (per ₹100)','pts'=>$earnActions['purchase_rate'],'icon'=>'🛍️'],
                    ] as $earn)
                    <div class="d-flex justify-content-between align-items-center mb-3 p-2 rounded-2 hover-bg">
                        <span>{{ $earn['icon'] }} {{ $earn['label'] }}</span>
                        <span class="badge bg-lumina-soft text-dark fw-bold px-3">+{{ $earn['pts'] }} pts</span>
                    </div>
                    @endforeach
                </div>
            </div>
        </div>

        {{-- Redeem section --}}
        <div class="col-lg-4 fade-in-up">
            <div class="card lumina-card shadow-sm h-100">
                <div class="card-body p-4">
                    <h5 class="fw-semibold mb-4">Redeem Points</h5>
                    @foreach($redeemOptions as $option)
                    <div class="redeem-option-card mb-3 p-3 border rounded-3">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <div>
                                <div class="fw-semibold">{{ $option['label'] }}</div>
                                <div class="text-muted small">{{ $option['description'] }}</div>
                            </div>
                            <span class="badge bg-warning text-dark">{{ number_format($option['points']) }} pts</span>
                        </div>
                        <form method="POST" action="{{ route('rewards.redeem') }}">
                            @csrf
                            <input type="hidden" name="reward_type" value="{{ $option['type'] }}">
                            <input type="hidden" name="points" value="{{ $option['points'] }}">
                            <button type="submit"
                                    class="btn btn-sm btn-lumina redeem-btn {{ $balance < $option['points'] ? 'disabled' : '' }}"
                                    {{ $balance < $option['points'] ? 'disabled' : '' }}>
                                Redeem
                            </button>
                        </form>
                    </div>
                    @endforeach
                </div>
            </div>
        </div>

        {{-- Points history --}}
        <div class="col-lg-4 fade-in-up">
            <div class="card lumina-card shadow-sm h-100">
                <div class="card-body p-4">
                    <h5 class="fw-semibold mb-4">Points History</h5>
                    @forelse($history as $log)
                    <div class="d-flex justify-content-between align-items-center mb-3 border-bottom pb-2">
                        <div>
                            <div class="small fw-medium">{{ $log->description }}</div>
                            <div class="text-muted" style="font-size:.72rem;">{{ $log->created_at->format('d M Y') }}</div>
                        </div>
                        <span class="fw-bold text-success">+{{ $log->points_earned }}</span>
                    </div>
                    @empty
                    <p class="text-muted text-center">No points history yet.<br>Start earning today!</p>
                    @endforelse
                    @if($history->hasPages())
                    <div class="mt-3">{{ $history->links() }}</div>
                    @endif
                </div>
            </div>
        </div>
    </div>
</div>
@endsection
