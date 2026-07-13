@extends('layouts.app')
@section('title', 'Membership Plans')

@section('content')
<div class="container py-5">
    <div class="text-center mb-5 fade-in-up">
        <span class="hero-badge mb-3 d-inline-block">⭐ Choose Your Plan</span>
        <h1 class="fw-bold mb-2">Lumina Membership</h1>
        <p class="text-muted fs-5">Unlock personalised AI recommendations matched to your budget and style</p>
    </div>

    <div class="row g-4 justify-content-center">
        @foreach($plans as $plan)
        @php $isCurrent = $currentTier === $plan->name; $isVip = $plan->name === 'vip'; @endphp
        <div class="col-md-4 fade-in-up">
            <div class="membership-plan-card h-100 {{ $isVip?'membership-vip':'' }} {{ $isCurrent?'membership-current':'' }}">
                @if($isCurrent)
                <div class="membership-current-badge">✓ Current Plan</div>
                @endif
                @if($isVip)
                <div class="membership-popular-badge">⭐ Premium</div>
                @endif

                <div class="plan-header text-center p-4 pb-3">
                    <div class="plan-icon mb-3">
                        @if($plan->name==='normal') 🌱
                        @elseif($plan->name==='medium') 💎
                        @else 👑
                        @endif
                    </div>
                    <h3 class="fw-bold mb-1">{{ $plan->display_name }}</h3>
                    <div class="plan-price my-3">
                        @if($plan->price == 0)
                            <span class="display-6 fw-bold">Free</span>
                        @else
                            <span class="display-6 fw-bold">₹{{ number_format($plan->price) }}</span>
                            <span class="text-muted">/month</span>
                        @endif
                    </div>
                    @if($plan->price_cap)
                    <div class="price-cap-badge">Products up to ₹{{ number_format($plan->price_cap) }}</div>
                    @else
                    <div class="price-cap-badge price-cap-vip">No price restrictions</div>
                    @endif
                </div>

                <div class="plan-features p-4 pt-0">
                    <ul class="list-unstyled mb-4">
                        @foreach($plan->features ?? [] as $feature)
                        <li class="d-flex align-items-start gap-2 mb-2">
                            <i class="bi bi-check-circle-fill text-success mt-1 flex-shrink-0"></i>
                            <span class="small">{{ $feature }}</span>
                        </li>
                        @endforeach
                    </ul>

                    @if($isCurrent)
                    <button class="btn btn-secondary w-100" disabled>Current Plan</button>
                    @elseif($plan->price == 0)
                    <a href="{{ route('dashboard') }}" class="btn btn-outline-lumina w-100">Get Started Free</a>
                    @else
                    <form method="POST" action="{{ route('memberships.subscribe') }}">
                        @csrf
                        <input type="hidden" name="plan_id" value="{{ $plan->id }}">
                        <button type="submit" class="btn {{ $isVip?'btn-lumina-gold':'btn-lumina' }} w-100">
                            Upgrade to {{ $plan->display_name }}
                        </button>
                    </form>
                    @endif
                </div>
            </div>
        </div>
        @endforeach
    </div>

    {{-- Brand examples per tier --}}
    <div class="row mt-5 g-4">
        @foreach(config('lumina.tiers') as $tierKey => $tierData)
        <div class="col-md-4 fade-in-up">
            <div class="card lumina-card h-100">
                <div class="card-body p-4">
                    <h6 class="fw-semibold mb-3 text-capitalize">{{ $tierData['label'] }} Brands</h6>
                    <div class="d-flex flex-wrap gap-2">
                        @foreach($tierData['brands'] as $brand)
                        <span class="badge bg-light text-dark border px-2 py-1">{{ $brand }}</span>
                        @endforeach
                    </div>
                </div>
            </div>
        </div>
        @endforeach
    </div>
</div>
@endsection
