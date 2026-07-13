@extends('layouts.app')
@section('title', 'Track Order '.$order->tracking_id)

@section('content')
<div class="container py-5">
    <div class="row justify-content-center">
        <div class="col-lg-7">
            <div class="text-center mb-5">
                <i class="bi bi-truck fs-1 text-lumina-primary mb-3 d-block"></i>
                <h2 class="fw-bold">Order Tracking</h2>
                <p class="text-muted">Tracking ID: <span class="fw-bold font-monospace">{{ $order->tracking_id }}</span></p>
            </div>

            <div class="card lumina-card shadow-sm mb-4">
                <div class="card-body p-4">
                    <div class="d-flex justify-content-between align-items-center mb-4 flex-wrap gap-2">
                        <div>
                            <h5 class="fw-semibold mb-0">Order #{{ $order->order_id }}</h5>
                            <div class="text-muted small">{{ $order->created_at->format('d M Y') }}</div>
                        </div>
                        <span class="badge fs-6 bg-{{ match($order->status) {
                            'delivered' => 'success', 'cancelled' => 'danger',
                            'shipped' => 'primary', default => 'warning'
                        } }} px-4 py-2">{{ ucwords(str_replace('_',' ',$order->status)) }}</span>
                    </div>

                    {{-- Progress steps --}}
                    @php
                        $steps = ['pending','processing','shipped','delivered'];
                        $currentIdx = array_search($order->status, $steps);
                    @endphp
                    <div class="tracking-steps d-flex justify-content-between position-relative mb-4">
                        <div class="tracking-line"></div>
                        @foreach($steps as $idx => $step)
                        @php $done = $currentIdx !== false && $idx <= $currentIdx; @endphp
                        <div class="tracking-step text-center flex-fill {{ $done ? 'done' : '' }}">
                            <div class="step-circle mb-2 {{ $done ? 'bg-lumina-primary text-white' : 'bg-light text-muted' }}">
                                <i class="bi bi-{{ match($step){ 'pending'=>'clock','processing'=>'gear','shipped'=>'truck','delivered'=>'check2-circle',default=>'circle' } }}"></i>
                            </div>
                            <div class="small fw-medium text-capitalize">{{ $step }}</div>
                        </div>
                        @endforeach
                    </div>

                    {{-- Items --}}
                    <h6 class="fw-semibold mb-3">Items</h6>
                    @foreach($order->items as $item)
                    <div class="d-flex gap-3 align-items-center mb-3">
                        <div class="fw-semibold small flex-grow-1">{{ $item->product_name }}</div>
                        <div class="text-muted small">× {{ $item->quantity }}</div>
                        <div class="fw-semibold small">₹{{ number_format($item->subtotal, 0) }}</div>
                    </div>
                    @endforeach

                    <hr>
                    <div class="d-flex justify-content-between fw-bold">
                        <span>Total</span>
                        <span class="text-lumina-primary">₹{{ number_format($order->total, 0) }}</span>
                    </div>
                </div>
            </div>

            {{-- Timeline --}}
            @if($order->statusLogs->count())
            <div class="card lumina-card shadow-sm">
                <div class="card-body p-4">
                    <h5 class="fw-semibold mb-4">Updates</h5>
                    @foreach($order->statusLogs->sortByDesc('created_at') as $log)
                    <div class="d-flex gap-3 mb-3">
                        <div class="text-lumina-primary flex-shrink-0 pt-1"><i class="bi bi-circle-fill" style="font-size:.5rem;"></i></div>
                        <div>
                            <div class="fw-semibold small">{{ ucwords(str_replace('_',' ',$log->status)) }}</div>
                            <div class="text-muted" style="font-size:.75rem;">{{ $log->created_at->format('d M Y, h:i A') }}</div>
                            @if($log->note)<div class="text-muted small">{{ $log->note }}</div>@endif
                        </div>
                    </div>
                    @endforeach
                </div>
            </div>
            @endif
        </div>
    </div>
</div>
@endsection

@push('styles')
<style>
.tracking-steps { gap:0; }
.tracking-line { position:absolute;top:20px;left:10%;width:80%;height:2px;background:#e0e0e0;z-index:0; }
.step-circle { width:40px;height:40px;border-radius:50%;display:flex;align-items:center;justify-content:center;margin:0 auto;position:relative;z-index:1;border:2px solid #e0e0e0; }
.tracking-step.done .step-circle { border-color:var(--lumina-primary); }
</style>
@endpush
