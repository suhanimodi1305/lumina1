@extends('layouts.app')
@section('title', $product->name)

@section('content')
<div class="container py-5">

    {{-- Breadcrumb --}}
    <nav aria-label="breadcrumb" class="mb-4">
        <ol class="breadcrumb small">
            <li class="breadcrumb-item"><a href="{{ route('products.index') }}">Products</a></li>
            <li class="breadcrumb-item"><a href="{{ route('products.index', ['category'=>$product->category?->slug]) }}">{{ $product->category?->name }}</a></li>
            <li class="breadcrumb-item active text-truncate" style="max-width:200px;">{{ $product->name }}</li>
        </ol>
    </nav>

    <div class="row g-5 mb-5">

        {{-- Image --}}
        <div class="col-lg-5 fade-in-up">
            <div class="product-detail-img-wrap rounded-4 overflow-hidden bg-light d-flex align-items-center justify-content-center" style="aspect-ratio:1;max-height:450px;">
                @if($product->image_url)
                <img src="{{ $product->image_url }}" class="img-fluid object-fit-contain p-3" alt="{{ $product->name }}" style="max-height:440px;">
                @else
                <i class="bi bi-bag text-muted" style="font-size:5rem;"></i>
                @endif
            </div>
        </div>

        {{-- Details --}}
        <div class="col-lg-7 fade-in-up">
            <div class="text-muted small mb-1">{{ $product->brand?->name }}</div>
            <h1 class="fw-bold fs-3 mb-2">{{ $product->name }}</h1>

            {{-- Rating --}}
            @if($product->rating > 0)
            <div class="d-flex align-items-center gap-2 mb-3">
                <div class="text-warning">
                    @for($i = 1; $i <= 5; $i++)
                        @if($i <= $product->rating)
                            <i class="bi bi-star-fill" style="font-size:.85rem;"></i>
                        @else
                            <i class="bi bi-star" style="font-size:.85rem;"></i>
                        @endif
                    @endfor
                </div>
                <span class="fw-semibold">{{ number_format($product->rating, 1) }}</span>
                <span class="text-muted small">({{ $product->reviews_count }} reviews)</span>
            </div>
            @endif

            {{-- Price --}}
            <div class="mb-4">
                <span class="fs-3 fw-bold text-lumina-primary">{{ $product->price_display }}</span>
                @if($product->offer_price && $product->price)
                <span class="text-muted text-decoration-line-through ms-2">₹{{ number_format($product->price, 0) }}</span>
                <span class="badge bg-success ms-2">{{ round((1 - $product->offer_price/$product->price)*100) }}% OFF</span>
                @endif
            </div>

            {{-- Description --}}
            @if($product->description)
            <p class="text-muted mb-4">{{ $product->description }}</p>
            @endif

            {{-- Tags --}}
            <div class="d-flex flex-wrap gap-2 mb-4">
                @foreach($product->suitable_for_skin_types ?? [] as $type)
                <span class="badge bg-light text-dark border">{{ ucfirst($type) }} Skin</span>
                @endforeach
                @foreach($product->skinConcerns as $concern)
                <span class="badge bg-lumina-soft text-dark">{{ $concern->name }}</span>
                @endforeach
            </div>

            {{-- Key ingredients --}}
            @if($product->key_ingredients_list)
            <div class="mb-4">
                <h6 class="fw-semibold mb-2">Key Ingredients</h6>
                <div class="d-flex flex-wrap gap-2">
                    @foreach($product->key_ingredients_list as $ingredient)
                    <span class="badge bg-success-soft text-success border border-success-subtle">{{ trim($ingredient) }}</span>
                    @endforeach
                </div>
            </div>
            @endif

            {{-- Add to cart --}}
            @if($product->availability === 'in_stock')
            <form method="POST" action="{{ route('cart.add') }}" class="d-flex gap-3 align-items-center mb-4">
                @csrf
                <input type="hidden" name="product_id" value="{{ $product->id }}">
                <div class="input-group" style="max-width:120px;">
                    <button type="button" class="btn btn-outline-secondary qty-btn" data-action="minus">−</button>
                    <input type="number" name="quantity" id="qty" class="form-control text-center" value="1" min="1" max="10">
                    <button type="button" class="btn btn-outline-secondary qty-btn" data-action="plus">+</button>
                </div>
                <button type="submit" class="btn btn-lumina px-4">
                    <i class="bi bi-bag-plus me-2"></i>Add to Cart
                </button>
                @if($product->affiliate_link)
                <a href="{{ $product->affiliate_link }}" target="_blank" rel="noopener" class="btn btn-outline-lumina">
                    Buy Online <i class="bi bi-box-arrow-up-right ms-1"></i>
                </a>
                @endif
            </form>
            @else
            <div class="alert alert-warning">Currently out of stock</div>
            @endif

            {{-- AI advice --}}
            @auth
            <a href="{{ route('chat.create', ['mode'=>'doctor']) }}" class="btn btn-outline-lumina btn-sm">
                <i class="bi bi-chat-heart me-2"></i>Ask Dr. Lumina about this product
            </a>
            @endauth
        </div>
    </div>

    {{-- Tabs: Full ingredients / Reviews --}}
    <ul class="nav nav-tabs mb-4" id="productTabs">
        <li class="nav-item"><button class="nav-link active" data-bs-toggle="tab" data-bs-target="#tab-ingredients">Full Ingredients</button></li>
        <li class="nav-item"><button class="nav-link" data-bs-toggle="tab" data-bs-target="#tab-reviews">Reviews ({{ $product->reviews_count }})</button></li>
    </ul>
    <div class="tab-content mb-5">
        <div class="tab-pane fade show active" id="tab-ingredients">
            <p class="text-muted small font-monospace">{{ $product->full_ingredients ?? 'Not available.' }}</p>
        </div>
        <div class="tab-pane fade" id="tab-reviews">
            @forelse($product->reviews as $review)
            <div class="border-bottom pb-3 mb-3">
                <div class="d-flex justify-content-between mb-1">
                    <span class="fw-semibold">{{ $review->user?->name ?? 'User' }}</span>
                    <span class="text-muted small">{{ $review->created_at->format('d M Y') }}</span>
                </div>
                <div class="text-warning mb-1">
                    @for($i=1;$i<=5;$i++)<i class="bi bi-star{{ $i<=$review->rating?'-fill':'' }}" style="font-size:.75rem;"></i>@endfor
                </div>
                <p class="mb-0 small">{{ $review->review_text }}</p>
            </div>
            @empty
            <p class="text-muted">No reviews yet. Be the first!</p>
            @endforelse
        </div>
    </div>

    {{-- Related products --}}
    @if($related->count())
    <h4 class="fw-bold mb-4">You Might Also Like</h4>
    <div class="row g-3">
        @foreach($related as $relProduct)
            @include('components.product-card', ['product' => $relProduct])
        @endforeach
    </div>
    @endif

</div>
@endsection

@push('scripts')
<script>
document.querySelectorAll('.qty-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        const input = document.getElementById('qty');
        const val = parseInt(input.value);
        if (this.dataset.action === 'plus' && val < 10) input.value = val + 1;
        if (this.dataset.action === 'minus' && val > 1) input.value = val - 1;
    });
});
</script>
@endpush
