@extends('layouts.app')
@section('title', 'Marketing Dashboard')

@section('content')
<div class="container-fluid py-4 px-4">

    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2 class="fw-bold mb-0"><i class="bi bi-megaphone me-2"></i>Marketing Dashboard</h2>
        <div class="d-flex gap-2">
            <a href="{{ route('marketing.campaigns.create') }}" class="btn btn-lumina btn-sm">
                <i class="bi bi-plus-lg me-1"></i>New Campaign
            </a>
            <a href="{{ route('marketing.coupons.create') }}" class="btn btn-outline-lumina btn-sm">
                <i class="bi bi-ticket-perforated me-1"></i>New Coupon
            </a>
        </div>
    </div>

    {{-- KPI cards --}}
    <div class="row g-3 mb-4">
        @foreach([
            ['label'=>'Active Campaigns', 'value'=>$stats['active_campaigns'],  'icon'=>'broadcast',             'color'=>'#c9a84c'],
            ['label'=>'Active Coupons',   'value'=>$stats['active_coupons'],    'icon'=>'ticket-perforated',     'color'=>'#7b68ee'],
            ['label'=>'Active Banners',   'value'=>$stats['active_banners'],    'icon'=>'image',                 'color'=>'#4a90d9'],
            ['label'=>'Impressions',      'value'=>number_format($stats['total_impressions']), 'icon'=>'eye',    'color'=>'#27ae60'],
            ['label'=>'Clicks',           'value'=>number_format($stats['total_clicks']),      'icon'=>'cursor', 'color'=>'#e67e22'],
            ['label'=>'Revenue (₹)',       'value'=>number_format($stats['total_revenue'], 0), 'icon'=>'cash',   'color'=>'#e74c3c'],
        ] as $kpi)
        <div class="col-6 col-md-4 col-xl-2 fade-in-up">
            <div class="card lumina-card shadow-sm text-center p-3">
                <i class="bi bi-{{ $kpi['icon'] }} fs-3 mb-2" style="color:{{ $kpi['color'] }}"></i>
                <div class="fw-bold fs-5">{{ $kpi['value'] }}</div>
                <div class="text-muted small">{{ $kpi['label'] }}</div>
            </div>
        </div>
        @endforeach
    </div>

    <div class="row g-4">

        {{-- Recent campaigns --}}
        <div class="col-lg-7">
            <div class="card lumina-card shadow-sm">
                <div class="card-body p-4">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <h5 class="fw-semibold mb-0">Recent Campaigns</h5>
                        <a href="{{ route('marketing.campaigns.index') }}" class="btn btn-sm btn-outline-secondary">View All</a>
                    </div>
                    @if($recentCampaigns->isEmpty())
                    <p class="text-muted">No campaigns yet.</p>
                    @else
                    <div class="table-responsive">
                        <table class="table table-sm align-middle">
                            <thead class="text-muted small">
                                <tr><th>Campaign</th><th>Status</th><th>Impressions</th><th>CTR</th><th>Revenue</th></tr>
                            </thead>
                            <tbody>
                                @foreach($recentCampaigns as $c)
                                <tr>
                                    <td>
                                        <div class="fw-semibold small">{{ Str::limit($c->name, 30) }}</div>
                                        <div class="text-muted" style="font-size:.7rem;">{{ $c->type }}</div>
                                    </td>
                                    <td>
                                        <span class="badge bg-{{ $c->status==='active'?'success':'secondary' }} text-capitalize">{{ $c->status }}</span>
                                    </td>
                                    <td class="small">{{ number_format($c->impressions) }}</td>
                                    <td class="small">
                                        {{ $c->impressions > 0 ? number_format($c->clicks/$c->impressions*100,1).'%' : '—' }}
                                    </td>
                                    <td class="small fw-semibold">₹{{ number_format($c->revenue, 0) }}</td>
                                </tr>
                                @endforeach
                            </tbody>
                        </table>
                    </div>
                    @endif
                </div>
            </div>
        </div>

        {{-- Active banners --}}
        <div class="col-lg-5">
            <div class="card lumina-card shadow-sm">
                <div class="card-body p-4">
                    <div class="d-flex justify-content-between align-items-center mb-3">
                        <h5 class="fw-semibold mb-0">Active Banners</h5>
                        <a href="{{ route('marketing.banners.create') }}" class="btn btn-sm btn-outline-secondary">
                            <i class="bi bi-plus-lg me-1"></i>Add
                        </a>
                    </div>
                    @if($activeBanners->isEmpty())
                    <p class="text-muted small">No active banners.</p>
                    @else
                    @foreach($activeBanners as $banner)
                    <div class="d-flex align-items-center gap-3 mb-3 p-2 border rounded-3">
                        @if($banner->image_url)
                        <img src="{{ $banner->image_url }}" style="width:60px;height:40px;object-fit:cover;border-radius:6px;" alt="{{ $banner->title }}">
                        @else
                        <div style="width:60px;height:40px;background:#f0f2f5;border-radius:6px;display:flex;align-items:center;justify-content:center;">
                            <i class="bi bi-image text-muted small"></i>
                        </div>
                        @endif
                        <div class="flex-grow-1">
                            <div class="fw-semibold small">{{ $banner->title }}</div>
                            <div class="text-muted" style="font-size:.7rem;">{{ $banner->placement }}</div>
                        </div>
                        <span class="badge bg-success text-capitalize">Active</span>
                    </div>
                    @endforeach
                    @endif
                </div>
            </div>
        </div>
    </div>
</div>
@endsection
