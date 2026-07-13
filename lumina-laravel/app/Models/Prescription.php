<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;

class Prescription extends Model
{
    public $timestamps = false;

    protected $fillable = [
        'appointment_id', 'doctor_id', 'patient_id',
        'file_path', 'notes', 'created_at',
    ];

    protected function casts(): array
    {
        return ['created_at' => 'datetime'];
    }

    public function appointment(): BelongsTo
    {
        return $this->belongsTo(Appointment::class);
    }

    public function doctor(): BelongsTo
    {
        return $this->belongsTo(DoctorProfile::class, 'doctor_id');
    }

    public function patient(): BelongsTo
    {
        return $this->belongsTo(User::class, 'patient_id');
    }

    public function getSignedUrlAttribute(): string
    {
        return \Storage::temporaryUrl(
            "private/{$this->file_path}",
            now()->addMinutes(30)
        );
    }
}
