<?php

namespace App\Http\Controllers\Orders;

use App\Http\Controllers\Controller;
use App\Models\Order;
use Illuminate\Http\Request;
use Illuminate\View\View;

class OrderController extends Controller
{
    public function show(Request $request, string $orderId): View
    {
        $order = Order::where('order_id', $orderId)
            ->with(['items', 'statusLogs'])
            ->firstOrFail();

        // Auth check: must be owner
        if ($request->user() && $order->user_id !== $request->user()->id) {
            abort(403);
        } elseif (!$request->user() && $order->user_id !== null) {
            abort(403);
        }

        return view('orders.show', compact('order'));
    }

    public function track(Request $request, string $trackingId): View
    {
        $order = Order::where('tracking_id', $trackingId)
            ->with(['items', 'statusLogs'])
            ->firstOrFail();

        return view('orders.track', compact('order'));
    }
}
