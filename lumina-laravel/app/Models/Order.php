<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Support\Str;

class Order extends Model
{
    protected $fillable = [
        'order_id', 'tracking_id', 'user_id',
        'full_name', 'phone', 'email',
        'address_line1', 'address_line2', 'city', 'state', 'pincode',
        'payment_method', 'payment_status', 'status',
        'subtotal', 'delivery_charge', 'discount', 'total',
        'estimated_delivery', 'delivered_at', 'order_notes',
    ];

    protected function casts(): array
    {
        return [
            'subtotal'           => 'decimal:2',
            'delivery_charge'    => 'decimal:2',
            'discount'           => 'decimal:2',
            'total'              => 'decimal:2',
            'estimated_delivery' => 'date',
            'delivered_at'       => 'datetime',
        ];
    }

    protected static function booted(): void
    {
        static::creating(function (Order $order): void {
            if (empty($order->order_id)) {
                $order->order_id = static::generateOrderId();
            }
            if (empty($order->tracking_id)) {
                $order->tracking_id = static::generateTrackingId();
            }
        });
    }

    // ── Relationships ─────────────────────────────────────────────────────

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    public function items(): HasMany
    {
        return $this->hasMany(OrderItem::class);
    }

    public function statusLogs(): HasMany
    {
        return $this->hasMany(OrderStatusLog::class)->orderByDesc('created_at');
    }

    public function requirements(): HasMany
    {
        return $this->hasMany(UserRequirement::class, 'linked_order_id');
    }

    // ── Helpers ───────────────────────────────────────────────────────────

    public static function generateOrderId(): string
    {
        $now    = now();
        $suffix = strtoupper(bin2hex(random_bytes(3)));

        return "OD{$now->format('ymdHis')}{$suffix}";
    }

    public static function generateTrackingId(): string
    {
        return strtoupper(substr(base64_encode(random_bytes(12)), 0, 16));
    }

    public function getStatusStepAttribute(): int
    {
        $steps = ['pending', 'confirmed', 'packed', 'shipped', 'out_for_delivery', 'delivered'];

        return (int) array_search($this->status, $steps, true);
    }

    public function getIsCodAttribute(): bool
    {
        return $this->payment_method === 'cod';
    }
}
