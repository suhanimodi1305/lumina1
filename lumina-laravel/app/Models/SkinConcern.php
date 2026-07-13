<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsToMany;

class SkinConcern extends Model
{
    public $timestamps = false;

    protected $fillable = ['name', 'slug', 'description', 'icon', 'created_at'];

    public function scanResults(): BelongsToMany
    {
        return $this->belongsToMany(ScanResult::class, 'scan_result_skin_concerns');
    }

    public function products(): BelongsToMany
    {
        return $this->belongsToMany(Product::class, 'product_skin_concerns');
    }
}
