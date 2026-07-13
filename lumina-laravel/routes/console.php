<?php

use Illuminate\Support\Facades\Schedule;

// ── Scheduled Jobs ────────────────────────────────────────────────────────────

// Daily makeup API sync at 2am
Schedule::command('makeup:sync')->dailyAt('02:00')->withoutOverlapping();

// Check and expire membership subscriptions every hour
Schedule::command('memberships:expire-check')->hourly();

// Clean up old demo scans (older than 7 days) nightly
Schedule::command('scans:cleanup-demo')->dailyAt('03:00');
