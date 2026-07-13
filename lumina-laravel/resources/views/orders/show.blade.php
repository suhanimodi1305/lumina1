@extends('layouts.app')
@section('title', 'Order '.$order->order_id)

@section('content')
<div class="container py-5">

    {{-- Header --}}
    <div class="d-flex justify-content-between align-items-start mb-4 flex-wrap gap-3">
        <div>
            <h2 class="fw-bold mb-1">Order #{{ $order->order_id }}</h2>
            <p class="text-muted mb-0">Placed on {{ $order->created_at->format('d M Y, h:i A') }}</p>
        </div>
        <div class="d-flex gap-2 align-items-center">
            <span class="badge fs-6 bg-{{ match($order->status) {
                'delivered' => 'success', 'cancelled' => 'danger',
                'shipped' => 'primary', 'processing' => 'warning',
                default => 'secondary'
            } }} px-4 py-2">{{ ucwords(str_replace('_',' ',$order->status)) }}</span>
        </div>
    </div>

    <div class="row g-4">

        {{-- Order items --}}
        <div class="col-lg-7">
            <div class="card lumina-card shadow-sm mb-4">
                <div class="card-body p-0">
                    <div class="p-4 border-bottom">
                        <h5 class="fw-semibold mb-0">Items Ordered</h5>
                    </div>
                    @foreach($order->items as $item)
                    <div class="d-flex align-items-center gap-3 p-4 border-bottom">
                        @if($item->image_url)
                        <img src="{{ $item->image_url }}" style="width:64px;height:64px;object-fit:cover;border-radius:10px;" alt="{{ $item->product_name }}">
                        @else
                        <div style="width:64px;height:64px;background:#f0f2f5;border-radius:10px;display:flex;align-items:center;justify-content:center;"><i class="bi bi-bag text-muted"></i></div>
                        @endif
                        <div class="flex-grow-1">
                            <h6 class="fw-semibold mb-1">{{ $item->product_name }}</h6>
                            <div class="text-muted small">{{ $item->brand_name }}</div>
                            @if($item->shade)<div class="text-muted small">Shade: {{ $item->shade }}</div>@endif
                        </div>
                        <div class="text-end">
                            <div class="fw-semibold">₹{{ number_format($item->unit_price, 0) }}</div>
                            <div class="text-muted small">× {{ $item->quantity }}</div>
                            <div class="fw-bold text-lumina-primary">₹{{ number_format($item->subtotal, 0) }}</div>
                        </div>
                    </div>
                    @endforeach
                    <div class="p-4">
                        <div class="d-flex justify-content-between mb-1">
                            <span class="text-muted">Subtotal</span>
                            <span>₹{{ number_format($order->subtotal, 0) }}</span>
                        </div>
                        <div class="d-flex justify-content-between mb-1">
                            <span class="text-muted">Delivery</span>
                            <span>{{ $order->delivery_charge == 0 ? 'Free' : '₹'.$order->delivery_charge }}</span>
                        </div>
                        @if($order->discount_amount > 0)
                        <div class="d-flex justify-content-between mb-1 text-success">
                            <span>Discount</span>
                            <span>−₹{{ number_format($order->discount_amount, 0) }}</span>
                        </div>
                        @endif
                        <hr>
                        <div class="d-flex justify-content-between fw-bold fs-6">
                            <span>Total Paid</span>
                            <span class="text-lumina-primary">₹{{ number_format($order->total, 0) }}</span>
                        </div>
                    </div>
                </div>
            </div>

            {{-- Status timeline --}}
            @if($order->statusLogs->count())
            <div class="card lumina-card shadow-sm">
                <div class="card-body p-4">
                    <h5 class="fw-semibold mb-4">Order Timeline</h5>
                    <div class="timeline">
                        @foreach($order->statusLogs->sortBy('created_at') as $log)
                        <div class="timeline-item d-flex gap-3 mb-3">
                            <div class="timeline-dot bg-lumina-primary rounded-circle flex-shrink-0 mt-1" style="width:12px;height:12px;"></div>
                            <div>
                                <div class="fw-semibold small">{{ ucwords(str_replace('_',' ',$log->status)) }}</div>
                                <div class="text-muted" style="font-size:.75rem;">{{ $log->created_at->format('d M Y, h:i A') }}</div>
                                @if($log->note)<div class="text-muted small">{{ $log->note }}</div>@endif
                            </div>
                        </div>
                        @endforeach
                    </div>
                </div>
            </div>
            @endif
        </div>

        {{-- Delivery info --}}
        <div class="col-lg-5">
            <div class="card lumina-card shadow-sm mb-4">
                <div class="card-body p-4">
                    <h5 class="fw-semibold mb-3">Delivery Address</h5>
                    <p class="fw-semibold mb-1">{{ $order->full_name }}</p>
                    <p class="text-muted small mb-1">{{ $order->address_line1 }}</p>
                    @if($order->address_line2)<p class="text-muted small mb-1">{{ $order->address_line2 }}</p>@endif
                    <p class="text-muted small mb-1">{{ $order->city }}, {{ $order->state }} — {{ $order->pincode }}</p>
                    <p class="text-muted small mb-0"><i class="bi bi-telephone me-1"></i>{{ $order->phone }}</p>
                </div>
            </div>

            <div class="card lumina-card shadow-sm mb-4">
                <div class="card-body p-4">
                    <h5 class="fw-semibold mb-3">Payment</h5>
                    <div class="d-flex justify-content-between mb-2">
                        <span class="text-muted">Method</span>
                        <span class="fw-semibold text-capitalize">{{ $order->payment_method }}</span>
                    </div>
                    <div class="d-flex justify-content-between">
                        <span class="text-muted">Status</span>
                        <span class="badge bg-{{ $order->payment_status === 'paid' ? 'success' : 'warning' }}">
                            {{ ucfirst($order->payment_status) }}
                        </span>
                    </div>
                </div>
            </div>

            @if($order->tracking_id)
            <div class="card lumina-card shadow-sm border-primary">
                <div class="card-body p-4">
                    <h5 class="fw-semibold mb-3"><i class="bi bi-truck text-primary me-2"></i>Tracking</h5>
                    <div class="bg-light rounded-3 p-3 text-center mb-3">
                        <span class="fw-bold font-monospace fs-6">{{ $order->tracking_id }}</span>
                    </div>
                    <a href="{{ route('orders.track', $order->tracking_id) }}" class="btn btn-outline-primary btn-sm w-100" target="_blank">
                        Track Public Link
                    </a>
                </div>
            </div>
            @endif
        </div>
    </div>
</div>
@endsection
