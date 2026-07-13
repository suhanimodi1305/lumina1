<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Concerns\HasUuids;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\BelongsTo;
use Illuminate\Database\Eloquent\Relations\HasMany;

class Conversation extends Model
{
    use HasUuids;

    const MODE_DOCTOR  = 'doctor';
    const MODE_MAKEUP  = 'makeup';
    const MODE_KBEAUTY = 'kbeauty';

    protected $fillable = [
        'user_id',
        'title',
        'mode',
        'scan_result_id',
        'is_vip_session',
    ];

    protected function casts(): array
    {
        return [
            'is_vip_session' => 'boolean',
        ];
    }

    // ── Relationships ─────────────────────────────────────────────────────

    public function user(): BelongsTo
    {
        return $this->belongsTo(User::class);
    }

    public function scanResult(): BelongsTo
    {
        return $this->belongsTo(ScanResult::class);
    }

    public function messages(): HasMany
    {
        return $this->hasMany(Message::class)->orderBy('created_at');
    }

    // ── Helpers ───────────────────────────────────────────────────────────

    public function messageCount(): int
    {
        return $this->messages()->count();
    }

    public function lastMessage(): ?Message
    {
        return $this->messages()->latest()->first();
    }
}
