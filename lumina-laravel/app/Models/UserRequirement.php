<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\BelongsToMany;

class UserRequirement extends Model
{
    protected $fillable = [
        'req_id', 'user_id', 'title',
        'custom_product', 'requirement_notes',
        'quantity', 'priority',
        'full_name', 'phone', 'email',
        'address_line1', 'address_line2', 'city', 'state', 'pincode',
        'status', 'assigned_to', 'employee_notes', 'linked_order_id',
    ];

    protected static function booted(): void
    {
        static::creating(function (UserRequirement $req): void {
            if (empty($req->req_id)) {
                $now    = now();
                $suffix = strtoupper(bin2hex(random_bytes(3)));
                $req->req_id = "REQ{$now->format('ymdHis')}{$suffix}";
            }
        });
    }

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    public function assignedTo(): BelongsTo
    {
        return $this->belongsTo(User::class, 'assigned_to');
    }

    public function linkedOrder(): BelongsTo
    {
        return $this->belongsTo(Order::class, 'linked_order_id');
    }

    public function products(): BelongsToMany
    {
        return $this->belongsToMany(Product::class, 'user_requirements_products');
    }

    public function getStatusColorAttribute(): string
    {
        return match ($this->status) {
            'pending'    => 'warning',
            'accepted'   => 'info',
            'processing' => 'primary',
            'dispatched' => 'secondary',
            'delivered'  => 'success',
            'rejected'   => 'danger',
            'cancelled'  => 'dark',
            default      => 'secondary',
        };
    }
}
