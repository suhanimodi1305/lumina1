@extends('layouts.app')
@section('title', 'Coupons')

@section('content')
<div class="container py-5">
    <div class="d-flex justify-content-between align-items-center mb-4">
        <h2 class="fw-bold mb-0"><i class="bi bi-ticket-perforated me-2"></i>Coupons</h2>
        <a href="{{ route('marketing.coupons.create') }}" class="btn btn-lumina">
            <i class="bi bi-plus-lg me-2"></i>New Coupon
        </a>
    </div>

    @if(session('success'))
    <div class="alert alert-success alert-dismissible fade show" role="alert">
        {{ session('success') }}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    </div>
    @endif

    <div class="card lumina-card shadow-sm">
        <div class="card-body p-0">
            @if($coupons->isEmpty())
            <div class="text-center py-5 text-muted">
                <i class="bi bi-ticket-perforated fs-1 d-block mb-2"></i>
                <p>No coupons yet. <a href="{{ route('marketing.coupons.create') }}">Create the first one.</a></p>
            </div>
            @else
            <div class="table-responsive">
                <table class="table table-hover align-middle mb-0">
                    <thead class="bg-light small text-muted">
                        <tr>
                            <th>Code</th>
                            <th>Discount</th>
                            <th>Min Order</th>
                            <th>Max Discount</th>
                            <th class="text-center">Usage</th>
                            <th>Expires</th>
                            <th class="text-center">Status</th>
                            <th class="text-end">Actions</th>
                        </tr>
                    </thead>
                    <tbody>
                        @foreach($coupons as $coupon)
                        <tr>
                            <td>
                                <span class="badge bg-dark font-monospace fs-6 px-3 py-2">{{ $coupon->code }}</span>
                            </td>
                            <td class="fw-semibold">
                                @if($coupon->discount_type === 'percent')
                                    {{ $coupon->discount_value }}% off
                                @else
                                    ₹{{ number_format($coupon->discount_value, 0) }} off
                                @endif
                            </td>
                            <td class="small">
                                {{ $coupon->min_order ? '₹'.number_format($coupon->min_order, 0) : '—' }}
                            </td>
                            <td class="small">
                                {{ $coupon->max_discount ? '₹'.number_format($coupon->max_discount, 0) : '—' }}
                            </td>
                            <td class="text-center small">
                                {{ $coupon->times_used ?? 0 }}
                                @if($coupon->usage_limit)
                                / {{ $coupon->usage_limit }}
                                @endif
                            </td>
                            <td class="small">
                                @if($coupon->expires_at)
                                    <span class="{{ $coupon->expires_at->isPast() ? 'text-danger' : '' }}">
                                        {{ $coupon->expires_at->format('d M Y') }}
                                    </span>
                                @else
                                    <span class="text-muted">Never</span>
                                @endif
                            </td>
                            <td class="text-center">
                                @if($coupon->is_active && (!$coupon->expires_at || $coupon->expires_at->isFuture()))
                                    <span class="badge bg-success">Active</span>
                                @elseif(!$coupon->is_active)
                                    <span class="badge bg-secondary">Disabled</span>
                                @else
                                    <span class="badge bg-danger">Expired</span>
                                @endif
                            </td>
                            <td class="text-end">
                                <a href="{{ route('marketing.coupons.edit', $coupon) }}"
                                   class="btn btn-sm btn-outline-secondary">Edit</a>
                                <form method="POST" action="{{ route('marketing.coupons.destroy', $coupon) }}"
                                      class="d-inline" onsubmit="return confirm('Delete coupon {{ $coupon->code }}?')">
                                    @csrf @method('DELETE')
                                    <button class="btn btn-sm btn-outline-danger">Delete</button>
                                </form>
                            </td>
                        </tr>
                        @endforeach
                    </tbody>
                </table>
            </div>
            @endif
        </div>
    </div>
    <div class="mt-4">{{ $coupons->links() }}</div>
</div>
@endsection
