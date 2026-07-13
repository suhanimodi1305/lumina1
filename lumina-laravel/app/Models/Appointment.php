<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Database\Eloquent\Relations\HasOne;

class Appointment extends Model
{
    protected $fillable = [
        'patient_id', 'doctor_id', 'scan_result_id',
        'appointment_date', 'slot_time', 'status', 'notes',
    ];

    protected function casts(): array
    {
        return [
            'appointment_date' => 'date',
            'slot_time'        => 'datetime',
        ];
    }

    public function patient(): BelongsTo
    {
        return $this->belongsTo(User::class, 'patient_id');
    }

    public function doctor(): BelongsTo
    {
        return $this->belongsTo(DoctorProfile::class, 'doctor_id');
    }

    public function scanResult(): BelongsTo
    {
        return $this->belongsTo(ScanResult::class);
    }

    public function messages(): HasMany
    {
        return $this->hasMany(AppointmentMessage::class)->orderBy('created_at');
    }

    public function prescription(): HasOne
    {
        return $this->hasOne(Prescription::class);
    }
}
