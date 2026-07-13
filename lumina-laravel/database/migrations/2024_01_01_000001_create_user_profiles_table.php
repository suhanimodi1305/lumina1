<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('user_profiles', function (Blueprint $table): void {
            $table->id();
            $table->foreignId('user_id')->constrained()->cascadeOnDelete();
            $table->enum('tier', ['normal', 'medium', 'vip'])->default('normal');
            $table->string('referral_code', 12)->unique();
            $table->unsignedInteger('loyalty_points')->default(0);
            $table->timestamp('tier_updated_at')->nullable();
            $table->timestamp('subscription_expires_at')->nullable();
            $table->enum('staff_role', ['none', 'marketing', 'admin', 'doctor', 'employee'])->default('none');
            $table->enum('admin_override_tier', ['normal', 'medium', 'vip'])->nullable();
            $table->boolean('admin_override_active')->default(false);
            $table->string('avatar')->nullable();
            $table->string('phone', 20)->nullable();
            $table->date('date_of_birth')->nullable();
            $table->enum('gender', ['male', 'female', 'other'])->nullable();
            $table->timestamps();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('user_profiles');
    }
};
