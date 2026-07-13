<?php

namespace App\Services;

use App\Models\Coupon;
use App\Models\Order;
use App\Models\OrderStatusLog;
use App\Models\User;
use Illuminate\Support\Facades\DB;

class OrderService
{
    public function __construct(private RewardsService $rewardsService) {}

    /**
     * Create an order from session cart data.
     */
    public function createFromCart(array $cart, array $address, string $paymentMethod, ?User $user, ?string $couponCode = null): Order
    {
        return DB::transaction(function () use ($cart, $address, $paymentMethod, $user, $couponCode): Order {
            $subtotal = collect($cart)->sum(fn ($item) => $item['price'] * $item['quantity']);
            $delivery = $subtotal >= 499 ? 0 : 49;
            $discount = 0;

            $coupon = null;
            if ($couponCode) {
                $coupon = Coupon::where('code', strtoupper($couponCode))->first();
                if ($coupon && $coupon->is_valid) {
                    $discount = $coupon->calculateDiscount($subtotal);
                }
            }

            $total = max(0, $subtotal + $delivery - $discount);

            $order = Order::create([
                'user_id'         => $user?->id,
                'full_name'       => $address['full_name'],
                'phone'           => $address['phone'],
                'email'           => $address['email'] ?? '',
                'address_line1'   => $address['address_line1'],
                'address_line2'   => $address['address_line2'] ?? '',
                'city'            => $address['city'],
                'state'           => $address['state'],
                'pincode'         => $address['pincode'],
                'payment_method'  => $paymentMethod,
                'payment_status'  => $paymentMethod === 'cod' ? 'pending' : 'pending',
                'status'          => 'pending',
                'subtotal'        => $subtotal,
                'delivery_charge' => $delivery,
                'discount'        => $discount,
                'total'           => $total,
                'estimated_delivery' => now()->addDays(5)->toDateString(),
            ]);

            // Create order items
            foreach ($cart as $item) {
                $order->items()->create([
                    'product_id' => $item['product_id'],
                    'name'       => $item['name'],
                    'brand'      => $item['brand'],
                    'image_url'  => $item['image_url'],
                    'sku'        => $item['sku'],
                    'shade'      => $item['shade'],
                    'price'      => $item['price'],
                    'quantity'   => $item['quantity'],
                ]);
            }

            // Initial status log
            OrderStatusLog::create([
                'order_id'   => $order->id,
                'status'     => 'pending',
                'message'    => 'Order placed successfully.',
                'location'   => '',
            ]);

            // Mark coupon as used
            if ($coupon && $user) {
                $coupon->increment('used_count');
                \App\Models\CouponUsage::create([
                    'coupon_id' => $coupon->id,
                    'user_id'   => $user->id,
                    'order_id'  => $order->id,
                ]);
            }

            // Award purchase points
            if ($user) {
                $this->rewardsService->awardPurchasePoints($user, (float) $total, $order->id);
            }

            return $order;
        });
    }
}
