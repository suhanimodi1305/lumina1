@extends('layouts.app')
@section('title', 'Your Cart')

@section('content')
<div class="container py-5">
    <h2 class="fw-bold mb-4">Shopping Cart</h2>

    @if(empty($cart))
    <div class="text-center py-5">
        <i class="bi bi-bag-x fs-1 text-muted mb-3 d-block"></i>
        <h5>Your cart is empty</h5>
        <p class="text-muted">Browse our products and add something you love.</p>
        <a href="{{ route('products.index') }}" class="btn btn-lumina">Shop Now</a>
    </div>
    @else
    @php $subtotal = collect($cart)->sum(fn($i) => $i['price'] * $i['quantity']); $deliveryCost = $subtotal >= 499 ? 0 : 49; $grandTotal = $subtotal + $deliveryCost; @endphp
    <div class="row g-4">

        {{-- Cart items --}}
        <div class="col-lg-8">
            <div class="card lumina-card shadow-sm">
                <div class="card-body p-0">
                    @foreach($cart as $cartKey => $item)
                    <div class="cart-row d-flex align-items-center gap-3 p-4 border-bottom" data-product="{{ $item['product_id'] }}">
                        <div class="cart-item-img flex-shrink-0">
                            @if($item['image_url'])
                            <img src="{{ $item['image_url'] }}" style="width:72px;height:72px;object-fit:cover;border-radius:10px;" alt="{{ $item['name'] }}">
                            @else
                            <div style="width:72px;height:72px;background:#f0f2f5;border-radius:10px;display:flex;align-items:center;justify-content:center;">
                                <i class="bi bi-bag text-muted"></i>
                            </div>
                            @endif
                        </div>
                        <div class="flex-grow-1">
                            <div class="text-muted small">{{ $item['brand'] }}</div>
                            <h6 class="fw-semibold mb-1">{{ $item['name'] }}</h6>
                            @if($item['shade'])<div class="text-muted small">Shade: {{ $item['shade'] }}</div>@endif
                            <div class="fw-bold text-lumina-primary">₹{{ number_format($item['price'], 0) }}</div>
                        </div>
                        <div class="d-flex align-items-center gap-2">
                            <div class="input-group input-group-sm" style="width:110px;">
                                <button class="btn btn-outline-secondary qty-btn" data-action="minus" data-key="{{ $cartKey }}">−</button>
                                <input type="number" class="form-control text-center qty-input" value="{{ $item['quantity'] }}" min="1" max="10" data-key="{{ $cartKey }}">
                                <button class="btn btn-outline-secondary qty-btn" data-action="plus" data-key="{{ $cartKey }}">+</button>
                            </div>
                            <button class="btn btn-sm btn-outline-danger remove-btn" data-key="{{ $cartKey }}">
                                <i class="bi bi-trash3"></i>
                            </button>
                        </div>
                        <div class="text-end fw-bold" style="min-width:80px;">
                            ₹{{ number_format($item['price'] * $item['quantity'], 0) }}
                        </div>
                    </div>
                    @endforeach
                </div>
            </div>
        </div>

        {{-- Summary --}}
        <div class="col-lg-4">
            <div class="card lumina-card shadow-sm">
                <div class="card-body p-4">
                    <h5 class="fw-semibold mb-4">Order Summary</h5>
                    <div class="d-flex justify-content-between mb-2">
                        <span class="text-muted">Subtotal</span>
                        <span class="fw-semibold">₹{{ number_format($subtotal, 0) }}</span>
                    </div>
                    <div class="d-flex justify-content-between mb-2">
                        <span class="text-muted">Delivery</span>
                        <span class="fw-semibold text-success">{{ $deliveryCost === 0 ? 'Free' : '₹'.$deliveryCost }}</span>
                    </div>
                    @if($subtotal < 499)
                    <div class="alert alert-info alert-sm py-2 small">
                        Add ₹{{ number_format(499 - $subtotal, 0) }} more for free delivery!
                    </div>
                    @endif
                    <hr>
                    <div class="d-flex justify-content-between mb-4">
                        <span class="fw-bold">Total</span>
                        <span class="fw-bold fs-5 text-lumina-primary">₹{{ number_format($grandTotal, 0) }}</span>
                    </div>
                    <a href="{{ route('checkout.index') }}" class="btn btn-lumina btn-lg w-100">
                        <i class="bi bi-lock me-2"></i>Proceed to Checkout
                    </a>
                    <a href="{{ route('products.index') }}" class="btn btn-outline-secondary w-100 mt-2">
                        Continue Shopping
                    </a>
                </div>
            </div>
        </div>
    </div>
    @endif
</div>
@endsection

@push('scripts')
<script>
const csrf = document.querySelector('meta[name=csrf-token]').content;

async function updateCart(cartKey, quantity) {
    await fetch('{{ route("cart.update") }}', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRF-TOKEN': csrf },
        body: JSON.stringify({ cart_key: cartKey, quantity })
    });
    location.reload();
}

document.querySelectorAll('.qty-btn').forEach(btn => {
    btn.addEventListener('click', function() {
        const key = this.dataset.key;
        const input = document.querySelector(`.qty-input[data-key="${key}"]`);
        let val = parseInt(input.value);
        if (this.dataset.action === 'plus' && val < 10) val++;
        else if (this.dataset.action === 'minus' && val > 1) val--;
        input.value = val;
        updateCart(key, val);
    });
});

document.querySelectorAll('.remove-btn').forEach(btn => {
    btn.addEventListener('click', async function() {
        await fetch('{{ route("cart.remove") }}', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRF-TOKEN': csrf },
            body: JSON.stringify({ cart_key: this.dataset.key })
        });
        location.reload();
    });
});
</script>
@endpush
