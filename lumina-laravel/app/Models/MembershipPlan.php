<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;

class MembershipPlan extends Model
{
    protected $fillable = [
        'name', 'display_name', 'price',
        'duration_days', 'features', 'price_cap', 'is_active',
    ];

    protected function casts(): array
    {
        return [
            'features'  => 'array',
            'price'     => 'decimal:2',
            'price_cap' => 'integer',
            'is_active' => 'boolean',
        ];
    }

    public function subscriptions(): HasMany
    {
        return $this->hasMany(Subscription::class, 'plan_id');
    }
}
