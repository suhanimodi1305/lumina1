<?php

namespace App\Http\Controllers\Orders;

use App\Http\Controllers\Controller;
use App\Services\OrderService;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\Request;
use Illuminate\View\View;

class CheckoutController extends Controller
{
    public function __construct(private OrderService $orderService) {}

    public function index(Request $request): View|RedirectResponse
    {
        $cart = session('cart', []);
        if (empty($cart)) {
            return redirect()->route('cart.index')->with('error', 'Your cart is empty.');
        }

        $subtotal = collect($cart)->sum(fn ($item) => $item['price'] * $item['quantity']);
        $delivery = $subtotal >= 499 ? 0 : 49;

        return view('orders.checkout', compact('cart', 'subtotal', 'delivery'));
    }

    public function store(Request $request): RedirectResponse
    {
        $cart = session('cart', []);
        if (empty($cart)) {
            return redirect()->route('cart.index')->with('error', 'Your cart is empty.');
        }

        $validated = $request->validate([
            'full_name'      => 'required|string|max:150',
            'phone'          => 'required|string|max:15',
            'email'          => 'nullable|email',
            'address_line1'  => 'required|string|max:250',
            'address_line2'  => 'nullable|string|max:250',
            'city'           => 'required|string|max:100',
            'state'          => 'required|string|max:100',
            'pincode'        => 'required|string|max:10|regex:/^\d{6}$/',
            'payment_method' => 'required|in:cod,upi,card,netbanking,wallet',
            'coupon_code'    => 'nullable|string|max:30',
        ]);

        $order = $this->orderService->createFromCart(
            $cart,
            $validated,
            $validated['payment_method'],
            $request->user(),
            $validated['coupon_code'] ?? null,
        );

        // Clear cart
        $request->session()->forget('cart');

        return redirect()->route('orders.show', $order->order_id)
            ->with('success', "Order {$order->order_id} placed successfully!");
    }
}
