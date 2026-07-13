<?php

namespace App\Http\Controllers\Orders;

use App\Http\Controllers\Controller;
use App\Models\Product;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;
use Illuminate\View\View;

class CartController extends Controller
{
    public function index(Request $request): View
    {
        $cart = session('cart', []);
        $total = collect($cart)->sum(fn ($item) => $item['price'] * $item['quantity']);
        return view('orders.cart', compact('cart', 'total'));
    }

    public function add(Request $request): JsonResponse
    {
        $request->validate([
            'product_id' => 'required|exists:products,id',
            'quantity'   => 'integer|min:1|max:10',
            'shade'      => 'nullable|string|max:100',
        ]);

        $product  = Product::findOrFail($request->input('product_id'));
        $quantity = (int) $request->input('quantity', 1);
        $shade    = $request->input('shade', '');
        $cartKey  = $product->id . '_' . $shade;

        $cart = session('cart', []);

        if (isset($cart[$cartKey])) {
            $cart[$cartKey]['quantity'] = min($cart[$cartKey]['quantity'] + $quantity, 10);
        } else {
            $cart[$cartKey] = [
                'product_id' => $product->id,
                'name'       => $product->name,
                'brand'      => $product->brand?->name ?? '',
                'sku'        => $product->sku,
                'shade'      => $shade,
                'price'      => (float) $product->effective_price,
                'image_url'  => $product->image_url ?? '',
                'quantity'   => $quantity,
            ];
        }

        session(['cart' => $cart]);

        $cartCount = collect($cart)->sum('quantity');

        return response()->json([
            'success'    => true,
            'message'    => "{$product->name} added to cart.",
            'cart_count' => $cartCount,
        ]);
    }

    public function update(Request $request): JsonResponse
    {
        $request->validate([
            'cart_key' => 'required|string',
            'quantity' => 'required|integer|min:0|max:10',
        ]);

        $cart    = session('cart', []);
        $cartKey = $request->input('cart_key');
        $qty     = (int) $request->input('quantity');

        if ($qty === 0) {
            unset($cart[$cartKey]);
        } elseif (isset($cart[$cartKey])) {
            $cart[$cartKey]['quantity'] = $qty;
        }

        session(['cart' => $cart]);

        $total     = collect($cart)->sum(fn ($item) => $item['price'] * $item['quantity']);
        $cartCount = collect($cart)->sum('quantity');

        return response()->json(compact('total', 'cartCount'));
    }

    public function remove(Request $request): JsonResponse
    {
        $request->validate(['cart_key' => 'required|string']);

        $cart = session('cart', []);
        unset($cart[$request->input('cart_key')]);
        session(['cart' => $cart]);

        return response()->json(['success' => true, 'cart_count' => collect($cart)->sum('quantity')]);
    }
}
