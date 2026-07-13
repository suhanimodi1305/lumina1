<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('scan_results', function (Blueprint $table): void {
            $table->id();
            $table->foreignId('user_id')->nullable()->constrained()->nullOnDelete();
            $table->string('session_key', 100)->nullable()->index();
            $table->boolean('is_demo')->default(false);
            $table->enum('gender', ['male', 'female', 'other'])->default('female');
            $table->string('scan_image')->nullable();

            // Basic attributes
            $table->enum('skin_tone', ['fair', 'light', 'medium', 'tan', 'deep'])->default('medium');
            $table->enum('undertone', ['warm', 'cool', 'neutral', 'olive'])->default('neutral');
            $table->enum('face_shape', ['oval', 'round', 'square', 'heart', 'oblong', 'rectangle', 'diamond', 'triangle'])->default('oval');
            $table->enum('skin_type', ['oily', 'dry', 'combination', 'normal'])->default('normal');

            // Ages
            $table->unsignedSmallInteger('skin_age')->default(25);
            $table->unsignedSmallInteger('real_age')->default(25);

            // Scores (0–100)
            $table->unsignedTinyInteger('harmony_score')->default(75);
            $table->unsignedTinyInteger('hydration_score')->default(60);
            $table->unsignedTinyInteger('pigmentation_score')->default(30);
            $table->unsignedTinyInteger('acne_score')->default(20);
            $table->unsignedTinyInteger('aging_score')->default(25);
            $table->unsignedTinyInteger('elasticity_score')->default(65);

            // HuggingFace results
            $table->string('hf_acne_severity', 20)->default('none');
            $table->string('hf_skin_type', 20)->default('normal');
            $table->string('hf_undertone', 20)->default('neutral');
            $table->float('hf_acne_confidence')->default(0.0);
            $table->float('hf_skin_type_confidence')->default(0.0);
            $table->float('hf_undertone_confidence')->default(0.0);
            $table->text('hf_acne_raw')->nullable();
            $table->text('hf_skin_type_raw')->nullable();
            $table->text('hf_undertone_raw')->nullable();

            // Facial zones JSON
            $table->json('facial_zones')->nullable();

            $table->timestamps();

            $table->index(['user_id', 'created_at']);
        });

        // Pivot: scan_results <-> skin_concerns
        Schema::create('scan_result_skin_concerns', function (Blueprint $table): void {
            $table->foreignId('scan_result_id')->constrained()->cascadeOnDelete();
            $table->foreignId('skin_concern_id')->constrained()->cascadeOnDelete();
            $table->primary(['scan_result_id', 'skin_concern_id']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('scan_result_skin_concerns');
        Schema::dropIfExists('scan_results');
    }
};
