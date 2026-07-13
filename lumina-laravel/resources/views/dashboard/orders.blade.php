@extends('layouts.app')
@section('title', 'My Orders')

@section('content')
<div class="container py-5">
    <h2 class="fw-bold mb-4">My Orders</h2>

    @if($orders->isEmpty())
    <div class="text-center py-5">
        <i class="bi bi-bag-x fs-1 text-muted mb-3 d-block"></i>
        <h5>No orders yet</h5>
        <p class="text-muted">Start shopping and your orders will appear here.</p>
        <a href="{{ route('products.index') }}" class="btn btn-lumina">Shop Now</a>
    </div>
    @else
    <div class="card lumina-card shadow-sm">
        <div class="card-body p-0">
            @foreach($orders as $order)
            <div class="order-row p-4 border-bottom d-flex flex-wrap align-items-center gap-3">
                <div class="flex-grow-1">
                    <div class="d-flex align-items-center gap-2 mb-1">
                        <h6 class="fw-semibold mb-0">{{ $order->order_id }}</h6>
                        <span class="badge bg-{{ match($order->status) {
                            'delivered'=>'success','cancelled'=>'danger','shipped'=>'primary',
                            'processing'=>'warning',default=>'secondary'
                        } }}">{{ ucwords(str_replace('_',' ',$order->status)) }}</span>
                    </div>
                    <p class="text-muted small mb-1">
                        {{ $order->created_at->format('d M Y') }} ·
                        {{ $order->items->count() }} item{{ $order->items->count()>1?'s':'' }} ·
                        ₹{{ number_format($order->total, 0) }}
                    </p>
                    <div class="d-flex flex-wrap gap-1">
                        @foreach($order->items->take(2) as $item)
                        <span class="badge bg-light text-dark border small">{{ Str::limit($item->product_name, 25) }}</span>
                        @endforeach
                        @if($order->items->count() > 2)
                        <span class="badge bg-light text-muted small">+{{ $order->items->count()-2 }} more</span>
                        @endif
                    </div>
                </div>
                <div class="d-flex gap-2">
                    <a href="{{ route('orders.show', $order->order_id) }}" class="btn btn-sm btn-outline-lumina">
                        View Details
                    </a>
                    @if($order->tracking_id)
                    <a href="{{ route('orders.track', $order->tracking_id) }}" class="btn btn-sm btn-outline-secondary">
                        <i class="bi bi-truck me-1"></i>Track
                    </a>
                    @endif
                </div>
            </div>
            @endforeach
        </div>
    </div>
    <div class="mt-4">{{ $orders->links() }}</div>
    @endif
</div>
@endsection
