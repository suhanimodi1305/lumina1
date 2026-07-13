<?php
/**
 * Lumina — API Routes
 * Consumed by AJAX calls from Blade/Vue components.
 * All routes are stateless (Sanctum token auth) except where noted.
 */

use App\Http\Controllers\Chat\ChatController;
use App\Http\Controllers\Orders\OrderController;
use App\Http\Controllers\Products\ProductController;
use App\Http\Controllers\Scanner\ScanController;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Route;

// ── Health check (no auth) ─────────────────────────────────────────────────
Route::get('/health', fn () => response()->json(['status' => 'ok', 'service' => 'laravel']))->name('api.health');

// ── Authenticated API (Sanctum) ────────────────────────────────────────────
Route::middleware('auth:sanctum')->group(function (): void {

    // Current user
    Route::get('/user', fn (Request $request) => $request->user())->name('api.user');

    // Products (read-only via API)
    Route::get('/products', [ProductController::class, 'apiIndex'])->name('api.products.index');
    Route::get('/products/{product:slug}', [ProductController::class, 'apiShow'])->name('api.products.show');

    // Scanner
    Route::get('/scans',       [ScanController::class, 'apiIndex'])->name('api.scans.index');
    Route::get('/scans/{scan}', [ScanController::class, 'apiShow'])->name('api.scans.show');

    // Chat (AJAX from Vue chat widget)
    Route::post('/conversations/{conversation}/messages', [ChatController::class, 'sendMessage'])
        ->name('api.chat.message')->middleware('throttle.chat');

    // Orders
    Route::get('/orders/{order:order_id}', [OrderController::class, 'apiShow'])->name('api.orders.show');
    Route::get('/track/{trackingId}',      [OrderController::class, 'apiTrack'])->name('api.orders.track');
});
