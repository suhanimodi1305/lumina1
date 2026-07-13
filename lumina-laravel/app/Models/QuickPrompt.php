<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class QuickPrompt extends Model
{
    public $timestamps = false;

    protected $fillable = ['prompt_text', 'category', 'sort_order', 'is_active', 'created_at'];

    protected function casts(): array
    {
        return ['is_active' => 'boolean'];
    }
}
