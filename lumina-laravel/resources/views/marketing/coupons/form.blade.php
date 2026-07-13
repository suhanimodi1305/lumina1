@extends('layouts.app')
@section('title', isset($coupon) ? 'Edit Coupon' : 'New Coupon')

@section('content')
<div class="container py-5" style="max-width:680px;">
    <div class="d-flex align-items-center gap-2 mb-4">
        <a href="{{ route('marketing.coupons.index') }}" class="btn btn-sm btn-outline-secondary">
            <i class="bi bi-arrow-left"></i>
        </a>
        <h2 class="fw-bold mb-0">{{ isset($coupon) ? 'Edit Coupon' : 'New Coupon' }}</h2>
    </div>

    @if($errors->any())
    <div class="alert alert-danger">
        <ul class="mb-0 ps-3">@foreach($errors->all() as $e)<li>{{ $e }}</li>@endforeach</ul>
    </div>
    @endif

    <div class="card lumina-card shadow-sm">
        <div class="card-body p-4">
            <form method="POST"
                  action="{{ isset($coupon) ? route('marketing.coupons.update', $coupon) : route('marketing.coupons.store') }}">
                @csrf
                @if(isset($coupon)) @method('PUT') @endif

                <div class="mb-3">
                    <label class="form-label fw-semibold">Coupon Code <span class="text-danger">*</span></label>
                    <input type="text" name="code"
                           class="form-control font-monospace text-uppercase @error('code') is-invalid @enderror"
                           value="{{ old('code', $coupon?->code) }}"
                           placeholder="e.g. SUMMER20" maxlength="30"
                           style="letter-spacing:.1em;" required>
                    @error('code')<div class="invalid-feedback">{{ $message }}</div>@enderror
                </div>

                <div class="row g-3 mb-3">
                    <div class="col-md-6">
                        <label class="form-label fw-semibold">Discount Type <span class="text-danger">*</span></label>
                        <select name="discount_type" id="discountType"
                                class="form-select @error('discount_type') is-invalid @enderror" required>
                            <option value="percent" {{ old('discount_type', $coupon?->discount_type) === 'percent' ? 'selected' : '' }}>
                                Percentage (%)
                            </option>
                            <option value="flat" {{ old('discount_type', $coupon?->discount_type) === 'flat' ? 'selected' : '' }}>
                                Flat Amount (₹)
                            </option>
                        </select>
                        @error('discount_type')<div class="invalid-feedback">{{ $message }}</div>@enderror
                    </div>
                    <div class="col-md-6">
                        <label class="form-label fw-semibold">Discount Value <span class="text-danger">*</span></label>
                        <div class="input-group">
                            <span class="input-group-text" id="discountPrefix">%</span>
                            <input type="number" name="discount_value"
                                   class="form-control @error('discount_value') is-invalid @enderror"
                                   value="{{ old('discount_value', $coupon?->discount_value) }}"
                                   min="1" step="0.01" required>
                            @error('discount_value')<div class="invalid-feedback">{{ $message }}</div>@enderror
                        </div>
                    </div>
                </div>

                <div class="row g-3 mb-3">
                    <div class="col-md-6">
                        <label class="form-label fw-semibold">Minimum Order (₹)</label>
                        <input type="number" name="min_order"
                               class="form-control @error('min_order') is-invalid @enderror"
                               value="{{ old('min_order', $coupon?->min_order) }}" min="0" step="0.01"
                               placeholder="No minimum">
                        @error('min_order')<div class="invalid-feedback">{{ $message }}</div>@enderror
                    </div>
                    <div class="col-md-6">
                        <label class="form-label fw-semibold">Max Discount (₹)</label>
                        <input type="number" name="max_discount"
                               class="form-control @error('max_discount') is-invalid @enderror"
                               value="{{ old('max_discount', $coupon?->max_discount) }}" min="0" step="0.01"
                               placeholder="No cap">
                        @error('max_discount')<div class="invalid-feedback">{{ $message }}</div>@enderror
                        <div class="form-text text-muted">Max cap for percentage discounts.</div>
                    </div>
                </div>

                <div class="row g-3 mb-4">
                    <div class="col-md-6">
                        <label class="form-label fw-semibold">Usage Limit</label>
                        <input type="number" name="usage_limit"
                               class="form-control @error('usage_limit') is-invalid @enderror"
                               value="{{ old('usage_limit', $coupon?->usage_limit) }}" min="1"
                               placeholder="Unlimited">
                        @error('usage_limit')<div class="invalid-feedback">{{ $message }}</div>@enderror
                    </div>
                    <div class="col-md-6">
                        <label class="form-label fw-semibold">Expiry Date</label>
                        <input type="date" name="expires_at"
                               class="form-control @error('expires_at') is-invalid @enderror"
                               value="{{ old('expires_at', $coupon?->expires_at?->format('Y-m-d')) }}">
                        @error('expires_at')<div class="invalid-feedback">{{ $message }}</div>@enderror
                    </div>
                </div>

                <div class="mb-4">
                    <div class="form-check form-switch">
                        <input class="form-check-input" type="checkbox" name="is_active" value="1" id="isActive"
                               {{ old('is_active', $coupon?->is_active ?? true) ? 'checked' : '' }}>
                        <label class="form-check-label fw-semibold" for="isActive">Active</label>
                    </div>
                </div>

                <div class="d-flex gap-2 justify-content-end">
                    <a href="{{ route('marketing.coupons.index') }}" class="btn btn-outline-secondary">Cancel</a>
                    <button type="submit" class="btn btn-lumina">
                        <i class="bi bi-check-lg me-1"></i>{{ isset($coupon) ? 'Update Coupon' : 'Create Coupon' }}
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>

<script>
document.addEventListener('DOMContentLoaded', function () {
    const typeSelect  = document.getElementById('discountType');
    const prefixEl    = document.getElementById('discountPrefix');

    function updatePrefix() {
        prefixEl.textContent = typeSelect.value === 'percent' ? '%' : '₹';
    }

    typeSelect.addEventListener('change', updatePrefix);
    updatePrefix();
});
</script>
@endsection
