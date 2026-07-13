@extends('layouts.app')
@section('title', 'Products')

@push('styles')
<style>
.filter-sidebar .form-check-label { cursor:pointer; font-size:.875rem; }
.filter-sidebar .filter-section { border-bottom:1px solid rgba(0,0,0,.07); padding-bottom:1rem; margin-bottom:1rem; }
.filter-count { font-size:.7rem; color:#aaa; }
</style>
@endpush

@section('content')
<div class="container-fluid py-4 px-4">
<div class="row g-4">

    {{-- Filter sidebar --}}
    <div class="col-lg-2 col-md-3 filter-sidebar d-none d-md-block">

        <div class="d-flex justify-content-between align-items-center mb-3">
            <h6 class="fw-semibold mb-0">Filters</h6>
            @if(array_filter($filters))
            <a href="{{ route('products.index') }}" class="btn btn-sm btn-link text-danger p-0">Clear all</a>
            @endif
        </div>

        <form method="GET" action="{{ route('products.index') }}" id="filter-form">

            {{-- Search --}}
            <div class="filter-section">
                <input type="text" name="search" class="form-control form-control-sm"
                       placeholder="Search products..." value="{{ $filters['search'] ?? '' }}">
            </div>

            {{-- Category --}}
            <div class="filter-section">
                <h6 class="fw-semibold mb-2 small text-uppercase text-muted">Category</h6>
                @foreach($categories as $cat)
                <div class="form-check mb-1">
                    <input class="form-check-input filter-check" type="radio" name="category"
                           id="cat_{{ $cat->id }}" value="{{ $cat->slug }}"
                           {{ ($filters['category'] ?? '') === $cat->slug ? 'checked' : '' }}>
                    <label class="form-check-label" for="cat_{{ $cat->id }}">{{ $cat->name }}</label>
                </div>
                @endforeach
            </div>

            {{-- Brand --}}
            <div class="filter-section">
                <h6 class="fw-semibold mb-2 small text-uppercase text-muted">Brand</h6>
                <div style="max-height:160px;overflow-y:auto;">
                @foreach($brands as $brand)
                <div class="form-check mb-1">
                    <input class="form-check-input filter-check" type="radio" name="brand"
                           id="brand_{{ $brand->id }}" value="{{ $brand->slug }}"
                           {{ ($filters['brand'] ?? '') === $brand->slug ? 'checked' : '' }}>
                    <label class="form-check-label" for="brand_{{ $brand->id }}">{{ $brand->name }}</label>
                </div>
                @endforeach
                </div>
            </div>

            {{-- Skin type --}}
            <div class="filter-section">
                <h6 class="fw-semibold mb-2 small text-uppercase text-muted">Skin Type</h6>
                @foreach(['oily','dry','combination','normal','sensitive'] as $st)
                <div class="form-check mb-1">
                    <input class="form-check-input filter-check" type="radio" name="skin_type"
                           id="st_{{ $st }}" value="{{ $st }}"
                           {{ ($filters['skin_type'] ?? '') === $st ? 'checked' : '' }}>
                    <label class="form-check-label" for="st_{{ $st }}">{{ ucfirst($st) }}</label>
                </div>
                @endforeach
            </div>

            {{-- Concern --}}
            <div class="filter-section">
                <h6 class="fw-semibold mb-2 small text-uppercase text-muted">Concern</h6>
                <div style="max-height:160px;overflow-y:auto;">
                @foreach($skinConcerns as $concern)
                <div class="form-check mb-1">
                    <input class="form-check-input filter-check" type="radio" name="concern"
                           id="c_{{ $concern->id }}" value="{{ $concern->slug }}"
                           {{ ($filters['concern'] ?? '') === $concern->slug ? 'checked' : '' }}>
                    <label class="form-check-label" for="c_{{ $concern->id }}">{{ $concern->name }}</label>
                </div>
                @endforeach
                </div>
            </div>

            <button type="submit" class="btn btn-lumina btn-sm w-100">Apply Filters</button>
        </form>
    </div>

    {{-- Products grid --}}
    <div class="col-lg-10 col-md-9">

        {{-- Top bar --}}
        <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-3">
            <div>
                <h4 class="fw-bold mb-0">Products</h4>
                <span class="text-muted small">{{ $products->total() }} items</span>
            </div>

            {{-- Range quick filters --}}
            <div class="d-flex gap-2 flex-wrap">
                @foreach(['All'=>'','Makeup'=>'makeup','K-Beauty'=>'korean','Ayurvedic'=>'ayurvedic','Pharmacy'=>'pharmacy'] as $label=>$val)
                <a href="{{ route('products.index', array_merge($filters, ['range'=>$val])) }}"
                   class="btn btn-sm {{ ($filters['range'] ?? '') === $val ? 'btn-lumina' : 'btn-outline-secondary' }}">
                    {{ $label }}
                </a>
                @endforeach
            </div>
        </div>

        {{-- Active filters --}}
        @if(array_filter($filters))
        <div class="d-flex flex-wrap gap-2 mb-3">
            @foreach(array_filter($filters) as $key => $value)
            <span class="badge bg-lumina-soft text-dark px-3 py-2">
                {{ ucfirst(str_replace('_',' ',$key)) }}: {{ $value }}
                <a href="{{ route('products.index', array_merge($filters, [$key=>null])) }}"
                   class="ms-1 text-muted text-decoration-none">×</a>
            </span>
            @endforeach
        </div>
        @endif

        @if($products->isEmpty())
        <div class="text-center py-5">
            <i class="bi bi-bag-x fs-1 text-muted mb-3 d-block"></i>
            <h5>No products found</h5>
            <p class="text-muted">Try adjusting your filters</p>
            <a href="{{ route('products.index') }}" class="btn btn-outline-lumina">Clear Filters</a>
        </div>
        @else
        <div class="row g-3">
            @foreach($products as $product)
                @include('components.product-card', ['product' => $product])
            @endforeach
        </div>

        <div class="mt-4">
            {{ $products->withQueryString()->links() }}
        </div>
        @endif
    </div>
</div>
</div>
@endsection

@push('scripts')
<script>
// Auto-submit filter form on radio change
document.querySelectorAll('.filter-check').forEach(el => {
    el.addEventListener('change', () => document.getElementById('filter-form').submit());
});
</script>
@endpush
