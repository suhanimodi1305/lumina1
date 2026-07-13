<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

class DoctorProfile extends Model
{
    protected $fillable = [
        'user_id', 'specialisation', 'bio', 'photo',
        'consultation_fee', 'experience_years',
        'available_days', 'slot_duration_minutes', 'is_active',
    ];

    protected function casts(): array
    {
        return [
            'available_days'      => 'array',
            'consultation_fee'    => 'decimal:2',
            'experience_years'    => 'integer',
            'slot_duration_minutes' => 'integer',
            'is_active'           => 'boolean',
        ];
    }

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    public function appointments(): HasMany
    {
        return $this->hasMany(Appointment::class, 'doctor_id');
    }
}
