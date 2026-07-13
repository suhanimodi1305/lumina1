<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\BelongsToMany;
use Illuminate\Database\Eloquent\Relations\HasMany;

class ScanResult extends Model
{
    protected $fillable = [
        'user_id',
        'session_key',
        'is_demo',
        'gender',
        'scan_image',
        'skin_tone',
        'undertone',
        'face_shape',
        'skin_type',
        'skin_age',
        'real_age',
        'harmony_score',
        'hydration_score',
        'pigmentation_score',
        'acne_score',
        'aging_score',
        'elasticity_score',
        'hf_acne_severity',
        'hf_skin_type',
        'hf_undertone',
        'hf_acne_confidence',
        'hf_skin_type_confidence',
        'hf_undertone_confidence',
        'hf_acne_raw',
        'hf_skin_type_raw',
        'hf_undertone_raw',
        'facial_zones',
    ];

    protected function casts(): array
    {
        return [
            'is_demo'                   => 'boolean',
            'facial_zones'              => 'array',
            'hf_acne_confidence'        => 'float',
            'hf_skin_type_confidence'   => 'float',
            'hf_undertone_confidence'   => 'float',
            'skin_age'                  => 'integer',
            'real_age'                  => 'integer',
            'harmony_score'             => 'integer',
            'hydration_score'           => 'integer',
            'pigmentation_score'        => 'integer',
            'acne_score'                => 'integer',
            'aging_score'               => 'integer',
            'elasticity_score'          => 'integer',
        ];
    }

    // ── Relationships ─────────────────────────────────────────────────────

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    public function detectedConcerns(): BelongsToMany
    {
        return $this->belongsToMany(SkinConcern::class, 'scan_result_skin_concerns');
    }

    public function conversations(): HasMany
    {
        return $this->hasMany(Conversation::class);
    }

    // ── Helpers ───────────────────────────────────────────────────────────

    /**
     * Build a context array suitable for sending to the AI service.
     */
    public function toAiContext(): array
    {
        return [
            'skin_tone'          => $this->skin_tone,
            'undertone'          => $this->undertone,
            'skin_type'          => $this->skin_type,
            'face_shape'         => $this->face_shape,
            'harmony_score'      => $this->harmony_score,
            'hf_acne_severity'   => $this->hf_acne_severity,
            'hf_skin_type'       => $this->hf_skin_type,
            'detected_concerns'  => $this->detectedConcerns->pluck('slug')->toArray(),
        ];
    }

    public function getScanImageUrlAttribute(): ?string
    {
        if (!$this->scan_image) {
            return null;
        }

        return \Storage::temporaryUrl(
            "private/{$this->scan_image}",
            now()->addMinutes(60)
        );
    }
}
