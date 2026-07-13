<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('membership_plans', function (Blueprint $table): void {
            $table->id();
            $table->enum('name', ['normal', 'medium', 'vip'])->unique();
            $table->string('display_name', 50);
            $table->decimal('price', 8, 2)->default(0);
            $table->unsignedSmallInteger('duration_days')->default(30);
            $table->json('features')->nullable();
            $table->unsignedInteger('price_cap')->nullable();
            $table->boolean('is_active')->default(true);
            $table->timestamps();
        });

        Schema::create('subscriptions', function (Blueprint $table): void {
            $table->id();
            $table->foreignId('user_id')->constrained()->cascadeOnDelete();
            $table->foreignId('plan_id')->constrained('membership_plans');
            $table->enum('status', ['active', 'expired', 'cancelled'])->default('active');
            $table->timestamp('starts_at');
            $table->timestamp('expires_at');
            $table->timestamps();

            $table->index(['user_id', 'status']);
        });

        Schema::create('referral_logs', function (Blueprint $table): void {
            $table->id();
            $table->foreignId('referrer_profile_id')->constrained('user_profiles')->cascadeOnDelete();
            $table->foreignId('referred_profile_id')->constrained('user_profiles')->cascadeOnDelete();
            $table->unsignedSmallInteger('points_awarded')->default(0);
            $table->enum('status', ['pending', 'confirmed', 'revoked'])->default('pending');
            $table->timestamp('created_at')->useCurrent();
        });

        Schema::create('tier_audit_logs', function (Blueprint $table): void {
            $table->id();
            $table->foreignId('profile_id')->constrained('user_profiles')->cascadeOnDelete();
            $table->foreignId('changed_by')->nullable()->constrained('users')->nullOnDelete();
            $table->string('previous_tier', 10);
            $table->string('new_tier', 10);
            $table->unsignedSmallInteger('points_deducted')->default(0);
            $table->string('reason', 100)->default('manual');
            $table->timestamp('created_at')->useCurrent();

            $table->index(['profile_id', 'created_at']);
        });

        Schema::create('loyalty_points_log', function (Blueprint $table): void {
            $table->id();
            $table->foreignId('user_id')->constrained()->cascadeOnDelete();
            $table->string('action', 30);
            $table->unsignedSmallInteger('points_earned');
            $table->string('description', 200)->nullable();
            $table->unsignedBigInteger('reference_id')->nullable();
            $table->timestamp('created_at')->useCurrent();

            $table->index(['user_id', 'created_at']);
            $table->index(['user_id', 'action', 'created_at']);
        });

        Schema::create('loyalty_redemptions', function (Blueprint $table): void {
            $table->id();
            $table->foreignId('user_id')->constrained()->cascadeOnDelete();
            $table->unsignedSmallInteger('points_spent');
            $table->string('reward_type', 50);
            $table->decimal('reward_value', 8, 2)->default(0);
            $table->foreignId('coupon_id')->nullable()->constrained()->nullOnDelete();
            $table->string('status', 20)->default('pending');
            $table->timestamp('created_at')->useCurrent();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('loyalty_redemptions');
        Schema::dropIfExists('loyalty_points_log');
        Schema::dropIfExists('tier_audit_logs');
        Schema::dropIfExists('referral_logs');
        Schema::dropIfExists('subscriptions');
        Schema::dropIfExists('membership_plans');
    }
};
