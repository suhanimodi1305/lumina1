<?php

use App\Http\Controllers\Auth\AuthenticatedSessionController;
use App\Http\Controllers\Chat\ChatController;
use App\Http\Controllers\Dashboard\DashboardController;
use App\Http\Controllers\Doctor\AppointmentController;
use App\Http\Controllers\Doctor\DoctorController;
use App\Http\Controllers\Employee\EmployeeController;
use App\Http\Controllers\HomeController;
use App\Http\Controllers\Marketing\MarketingController;
use App\Http\Controllers\Memberships\MembershipController;
use App\Http\Controllers\Orders\CartController;
use App\Http\Controllers\Orders\CheckoutController;
use App\Http\Controllers\Orders\OrderController;
use App\Http\Controllers\Products\ProductController;
use App\Http\Controllers\Rewards\RewardsController;
use App\Http\Controllers\Scanner\ScanController;
use Illuminate\Support\Facades\Route;

// ── Public routes ──────────────────────────────────────────────────────────────
Route::get('/', [HomeController::class, 'index'])->name('home');

Route::get('/scan', [ScanController::class, 'upload'])->name('scan.upload');
Route::post('/scan', [ScanController::class, 'process'])->name('scan.process')
    ->middleware('throttle.scan');
Route::get('/scan/demo', [ScanController::class, 'demo'])->name('scan.demo');
Route::get('/results/{scanResult}', [ScanController::class, 'results'])->name('results.show');

Route::get('/products', [ProductController::class, 'index'])->name('products.index');
Route::get('/products/{product:slug}', [ProductController::class, 'show'])->name('products.show');

Route::get('/track/{trackingId}', [OrderController::class, 'track'])->name('orders.track');

Route::get('/doctor', [DoctorController::class, 'landing'])->name('doctor.landing');

// ── Auth (Laravel Breeze) ─────────────────────────────────────────────────────
require __DIR__.'/auth.php';

// ── Authenticated routes ──────────────────────────────────────────────────────
Route::middleware(['auth', 'verified'])->group(function (): void {

    // ── Personal dashboard ──────────────────────────────────────────────────
    Route::get('/me', [DashboardController::class, 'home'])->name('dashboard');
    Route::get('/me/scans', [DashboardController::class, 'scans'])->name('dashboard.scans');
    Route::get('/me/orders', [DashboardController::class, 'orders'])->name('dashboard.orders');
    Route::get('/me/profile', [DashboardController::class, 'profile'])->name('dashboard.profile');
    Route::put('/me/profile', [DashboardController::class, 'updateProfile'])->name('dashboard.profile.update');

    // ── Rewards ──────────────────────────────────────────────────────────────
    Route::get('/rewards', [RewardsController::class, 'index'])->name('rewards.index');
    Route::post('/rewards/redeem', [RewardsController::class, 'redeem'])->name('rewards.redeem');

    // ── Chat ────────────────────────────────────────────────────────────────
    Route::get('/chat', [ChatController::class, 'index'])->name('chat.index');
    Route::get('/chat/new', [ChatController::class, 'create'])->name('chat.create');
    Route::get('/chat/{conversation}', [ChatController::class, 'room'])->name('chat.room');
    Route::post('/chat/{conversation}/message', [ChatController::class, 'sendMessage'])
        ->name('chat.message')->middleware('throttle.chat');
    Route::post('/chat/{conversation}/photo', [ChatController::class, 'sendPhoto'])
        ->name('chat.photo');
    Route::post('/chat/{conversation}/mode', [ChatController::class, 'switchMode'])
        ->name('chat.mode');
    Route::delete('/chat/{conversation}', [ChatController::class, 'destroy'])
        ->name('chat.destroy');

    // ── Orders / Cart ────────────────────────────────────────────────────────
    Route::get('/cart', [CartController::class, 'index'])->name('cart.index');
    Route::post('/cart/add', [CartController::class, 'add'])->name('cart.add');
    Route::post('/cart/update', [CartController::class, 'update'])->name('cart.update');
    Route::post('/cart/remove', [CartController::class, 'remove'])->name('cart.remove');
    Route::get('/checkout', [CheckoutController::class, 'index'])->name('checkout.index');
    Route::post('/checkout', [CheckoutController::class, 'store'])->name('checkout.store');
    Route::get('/orders/{order:order_id}', [OrderController::class, 'show'])->name('orders.show');

    // ── Memberships ──────────────────────────────────────────────────────────
    Route::get('/membership', [MembershipController::class, 'index'])->name('memberships.index');
    Route::post('/membership/subscribe', [MembershipController::class, 'subscribe'])
        ->name('memberships.subscribe');

    // ── Doctor consultation ──────────────────────────────────────────────────
    Route::get('/doctor/book', [AppointmentController::class, 'book'])->name('doctor.book');
    Route::post('/doctor/book', [AppointmentController::class, 'store'])->name('doctor.store');
    Route::get('/doctor/consultation/{appointment}', [AppointmentController::class, 'room'])
        ->name('doctor.room');
    Route::post('/doctor/consultation/{appointment}/message', [AppointmentController::class, 'sendMessage'])
        ->name('doctor.message');
    Route::get('/me/appointments', [AppointmentController::class, 'index'])
        ->name('appointments.index');

    // ── Employee portal ──────────────────────────────────────────────────────
    Route::middleware('role:employee|admin')->prefix('employee')->name('employee.')->group(function (): void {
        Route::get('/', [EmployeeController::class, 'dashboard'])->name('dashboard');
        Route::get('/requirements', [EmployeeController::class, 'requirements'])->name('requirements');
        Route::post('/requirements/{requirement}/status', [EmployeeController::class, 'updateStatus'])
            ->name('requirements.status');
    });

    // ── Marketing dashboard ───────────────────────────────────────────────────
    Route::middleware('role:marketing|admin')->prefix('marketing')->name('marketing.')->group(function (): void {
        Route::get('/', [MarketingController::class, 'dashboard'])->name('dashboard');
        Route::resource('campaigns', \App\Http\Controllers\Marketing\CampaignController::class);
        Route::resource('banners', \App\Http\Controllers\Marketing\BannerController::class);
        Route::resource('coupons', \App\Http\Controllers\Marketing\CouponController::class);
    });
});
