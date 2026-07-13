<div class="col-6 col-md-4 col-lg-3 fade-in-up">
    <div class="product-card h-100">
        <div class="product-img-wrap position-relative">
            @if($product->image_url)
            <img src="{{ $product->image_url }}" class="product-img" alt="{{ $product->name }}" loading="lazy">
            @else
            <div class="product-img-placeholder"><i class="bi bi-bag text-muted"></i></div>
            @endif
            @if($product->offer_price && $product->price)
            <span class="product-discount-badge">
                {{ round((1 - $product->offer_price/$product->price)*100) }}% OFF
            </span>
            @endif
            @if($product->is_featured)
            <span class="product-featured-badge">⭐</span>
            @endif
        </div>
        <div class="product-info p-3">
            <div class="product-brand text-muted small mb-1">{{ $product->brand?->name ?? '' }}</div>
            <h6 class="product-name fw-semibold mb-2 lh-sm">
                <a href="{{ route('products.show', $product) }}" class="stretched-link text-dark text-decoration-none">
                    {{ Str::limit($product->name, 45) }}
                </a>
            </h6>
            <div class="d-flex align-items-center gap-2 mb-2">
                @if($product->rating > 0)
                <div class="product-rating">
                    <i class="bi bi-star-fill text-warning" style="font-size:.7rem;"></i>
                    <span class="small">{{ number_format($product->rating, 1) }}</span>
                    <span class="text-muted" style="font-size:.7rem;">({{ $product->reviews_count }})</span>
                </div>
                @endif
            </div>
            <div class="product-price d-flex align-items-center gap-2">
                <span class="fw-bold text-lumina-primary">
                    {{ $product->price_display }}
                </span>
                @if($product->offer_price && $product->price)
                <span class="text-muted text-decoration-line-through small">₹{{ number_format($product->price, 0) }}</span>
                @endif
            </div>
        </div>
        <div class="product-card-actions p-3 pt-0">
            <form method="POST" action="{{ route('cart.add') }}">
                @csrf
                <input type="hidden" name="product_id" value="{{ $product->id }}">
                <button type="submit" class="btn btn-sm btn-lumina w-100 add-cart-btn">
                    <i class="bi bi-bag-plus me-1"></i>Add to Cart
                </button>
            </form>
        </div>
    </div>
</div>
