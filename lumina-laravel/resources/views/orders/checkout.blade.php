@extends('layouts.app')
@section('title', 'Checkout')

@section('content')
<div class="container py-5">
    <h2 class="fw-bold mb-4">Checkout</h2>

    <form method="POST" action="{{ route('checkout.store') }}" id="checkout-form">
    @csrf
    <div class="row g-4">

        {{-- Delivery details --}}
        <div class="col-lg-7">
            <div class="card lumina-card shadow-sm mb-4">
                <div class="card-body p-4">
                    <h5 class="fw-semibold mb-4">Delivery Address</h5>
                    <div class="row g-3">
                        <div class="col-md-6">
                            <label class="form-label">Full Name *</label>
                            <input type="text" name="full_name" class="form-control @error('full_name') is-invalid @enderror"
                                   value="{{ old('full_name', auth()->user()->name) }}" required>
                            @error('full_name')<div class="invalid-feedback">{{ $message }}</div>@enderror
                        </div>
                        <div class="col-md-6">
                            <label class="form-label">Phone *</label>
                            <input type="tel" name="phone" class="form-control @error('phone') is-invalid @enderror"
                                   value="{{ old('phone', auth()->user()->profile?->phone) }}" required>
                            @error('phone')<div class="invalid-feedback">{{ $message }}</div>@enderror
                        </div>
                        <div class="col-12">
                            <label class="form-label">Email</label>
                            <input type="email" name="email" class="form-control"
                                   value="{{ old('email', auth()->user()->email) }}">
                        </div>
                        <div class="col-12">
                            <label class="form-label">Address Line 1 *</label>
                            <input type="text" name="address_line1" class="form-control @error('address_line1') is-invalid @enderror"
                                   value="{{ old('address_line1') }}" placeholder="House/Flat No, Street" required>
                            @error('address_line1')<div class="invalid-feedback">{{ $message }}</div>@enderror
                        </div>
                        <div class="col-12">
                            <label class="form-label">Address Line 2</label>
                            <input type="text" name="address_line2" class="form-control"
                                   value="{{ old('address_line2') }}" placeholder="Area, Landmark (optional)">
                        </div>
                        <div class="col-md-5">
                            <label class="form-label">City *</label>
                            <input type="text" name="city" class="form-control @error('city') is-invalid @enderror"
                                   value="{{ old('city') }}" required>
                            @error('city')<div class="invalid-feedback">{{ $message }}</div>@enderror
                        </div>
                        <div class="col-md-4">
                            <label class="form-label">State *</label>
                            <input type="text" name="state" class="form-control @error('state') is-invalid @enderror"
                                   value="{{ old('state') }}" required>
                            @error('state')<div class="invalid-feedback">{{ $message }}</div>@enderror
                        </div>
                        <div class="col-md-3">
                            <label class="form-label">Pincode *</label>
                            <input type="text" name="pincode" class="form-control @error('pincode') is-invalid @enderror"
                                   value="{{ old('pincode') }}" maxlength="6" required>
                            @error('pincode')<div class="invalid-feedback">{{ $message }}</div>@enderror
                        </div>
                    </div>
                </div>
            </div>

            {{-- Payment method --}}
            <div class="card lumina-card shadow-sm">
                <div class="card-body p-4">
                    <h5 class="fw-semibold mb-4">Payment Method</h5>
                    <div class="row g-3">
                        @foreach(['upi'=>['icon'=>'bi-phone','label'=>'UPI / PhonePe / GPay'],'cod'=>['icon'=>'bi-cash-coin','label'=>'Cash on Delivery'],'card'=>['icon'=>'bi-credit-card','label'=>'Credit / Debit Card'],'netbanking'=>['icon'=>'bi-bank','label'=>'Net Banking'],'wallet'=>['icon'=>'bi-wallet2','label'=>'Wallet']] as $method=>$info)
                        <div class="col-6 col-md-4">
                            <div class="payment-method-card border rounded-3 p-3 text-center {{ old('payment_method') === $method ? 'selected' : '' }}">
                                <input type="radio" name="payment_method" id="pay_{{ $method }}" value="{{ $method }}" class="d-none payment-radio" {{ old('payment_method','upi') === $method ? 'checked' : '' }}>
                                <label class="cursor-pointer w-100" for="pay_{{ $method }}">
                                    <i class="bi {{ $info['icon'] }} fs-4 d-block mb-1"></i>
                                    <span class="small fw-medium">{{ $info['label'] }}</span>
                                </label>
                            </div>
                        </div>
                        @endforeach
                    </div>
                    @error('payment_method')<div class="text-danger small mt-2">{{ $message }}</div>@enderror
                </div>
            </div>
        </div>

        {{-- Order summary --}}
        <div class="col-lg-5">
            <div class="card lumina-card shadow-sm sticky-top" style="top:90px;">
                <div class="card-body p-4">
                    <h5 class="fw-semibold mb-4">Order Summary</h5>

                    {{-- Cart items --}}
                    <div class="mb-4">
                        @foreach($cart as $item)
                        <div class="d-flex justify-content-between align-items-center mb-2 small">
                            <span class="text-truncate" style="max-width:70%;">{{ $item['name'] }} × {{ $item['quantity'] }}</span>
                            <span class="fw-semibold">₹{{ number_format($item['price'] * $item['quantity'], 0) }}</span>
                        </div>
                        @endforeach
                    </div>

                    <hr>
                    <div class="d-flex justify-content-between mb-2">
                        <span class="text-muted">Subtotal</span>
                        <span>₹{{ number_format($subtotal, 0) }}</span>
                    </div>
                    <div class="d-flex justify-content-between mb-2">
                        <span class="text-muted">Delivery</span>
                        <span class="text-success">{{ $delivery === 0 ? 'Free' : '₹'.$delivery }}</span>
                    </div>

                    {{-- Coupon --}}
                    <div class="input-group input-group-sm mb-3">
                        <input type="text" name="coupon_code" class="form-control" placeholder="Coupon code" value="{{ old('coupon_code') }}">
                        <button type="button" class="btn btn-outline-secondary">Apply</button>
                    </div>

                    <hr>
                    <div class="d-flex justify-content-between mb-4 fs-6 fw-bold">
                        <span>Total</span>
                        <span class="text-lumina-primary">₹{{ number_format($subtotal + $delivery, 0) }}</span>
                    </div>

                    <button type="submit" class="btn btn-lumina btn-lg w-100">
                        <i class="bi bi-lock me-2"></i>Place Order
                    </button>
                    <p class="text-muted text-center small mt-3">
                        <i class="bi bi-shield-check me-1"></i>Secured & encrypted checkout
                    </p>
                </div>
            </div>
        </div>

    </div>
    </form>
</div>
@endsection

@push('styles')
<style>
.payment-method-card { cursor:pointer; transition:.2s; }
.payment-method-card:hover, .payment-method-card.selected { border-color:var(--lumina-primary)!important; background:rgba(var(--lumina-primary-rgb),.05); }
</style>
@endpush

@push('scripts')
<script>
document.querySelectorAll('.payment-radio').forEach(radio => {
    radio.addEventListener('change', function() {
        document.querySelectorAll('.payment-method-card').forEach(c => c.classList.remove('selected'));
        this.closest('.payment-method-card').classList.add('selected');
    });
});
</script>
@endpush
