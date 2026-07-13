<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('conversations', function (Blueprint $table): void {
            $table->uuid('id')->primary();
            $table->foreignId('user_id')->constrained()->cascadeOnDelete();
            $table->string('title', 200)->default('New Consultation');
            $table->enum('mode', ['doctor', 'makeup', 'kbeauty'])->default('doctor');
            $table->foreignId('scan_result_id')->nullable()->constrained()->nullOnDelete();
            $table->boolean('is_vip_session')->default(false);
            $table->timestamps();

            $table->index(['user_id', 'updated_at']);
        });

        Schema::create('messages', function (Blueprint $table): void {
            $table->uuid('id')->primary();
            $table->foreignUuid('conversation_id')->constrained()->cascadeOnDelete();
            $table->enum('role', ['user', 'assistant']);
            $table->text('content');
            $table->longText('image_data')->nullable();
            $table->timestamp('created_at')->useCurrent();

            $table->index(['conversation_id', 'created_at']);
        });

        Schema::create('quick_prompts', function (Blueprint $table): void {
            $table->id();
            $table->string('prompt_text', 200);
            $table->string('category', 50)->nullable();
            $table->unsignedSmallInteger('sort_order')->default(0);
            $table->boolean('is_active')->default(true);
            $table->timestamp('created_at')->useCurrent();
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('quick_prompts');
        Schema::dropIfExists('messages');
        Schema::dropIfExists('conversations');
    }
};
