<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('brands', function (Blueprint $table): void {
            $table->id();
            $table->string('name', 100);
            $table->string('slug', 100)->unique();
            $table->text('description')->nullable();
            $table->string('logo_url')->nullable();
            $table->string('country_of_origin', 100)->nullable();
            $table->string('website')->nullable();
            $table->boolean('is_active')->default(true);
            $table->timestamps();
        });

        Schema::create('categories', function (Blueprint $table): void {
            $table->id();
            $table->string('name', 100);
            $table->string('slug', 100)->unique();
            $table->enum('type', ['makeup', 'korean', 'ayurvedic', 'pharmacy', 'treatment']);
            $table->text('description')->nullable();
            $table->string('icon', 50)->nullable();
            $table->unsignedSmallInteger('sort_order')->default(0);
            $table->boolean('is_active')->default(true);
            $table->timestamps();
        });

        Schema::create('subcategories', function (Blueprint $table): void {
            $table->id();
            $table->foreignId('category_id')->constrained()->cascadeOnDelete();
            $table->string('name', 100);
            $table->string('slug', 100)->unique();
            $table->text('description')->nullable();
            $table->unsignedSmallInteger('sort_order')->default(0);
            $table->boolean('is_active')->default(true);
            $table->timestamps();
        });

        Schema::create('products', function (Blueprint $table): void {
            $table->id();
            $table->foreignId('brand_id')->constrained()->restrictOnDelete();
            $table->foreignId('category_id')->constrained()->restrictOnDelete();
            $table->foreignId('subcategory_id')->nullable()->constrained()->nullOnDelete();
            $table->string('name', 200);
            $table->string('slug', 200)->unique();
            $table->string('sku', 50)->unique();
            $table->enum('product_range', ['makeup', 'korean', 'ayurvedic', 'pharmacy', 'treatment']);
            $table->text('description')->nullable();
            $table->text('key_ingredients')->nullable();
            $table->text('full_ingredients')->nullable();
            $table->decimal('price', 10, 2)->nullable();
            $table->decimal('offer_price', 10, 2)->nullable();
            $table->string('affiliate_link')->nullable();
            $table->json('suitable_for_skin_types')->nullable();
            $table->json('targets')->nullable();
            $table->json('shades_available')->nullable();
            $table->enum('undertone_match', ['warm', 'cool', 'neutral', 'olive'])->nullable();
            $table->enum('skin_tone_match', ['fair', 'light', 'medium', 'tan', 'deep'])->nullable();
            $table->string('coverage', 50)->nullable();
            $table->string('finish', 50)->nullable();
            $table->string('image_url')->nullable();
            $table->decimal('rating', 3, 2)->default(0);
            $table->unsignedInteger('reviews_count')->default(0);
            $table->enum('availability', ['in_stock', 'out_of_stock', 'discontinued'])->default('in_stock');
            $table->unsignedTinyInteger('ai_recommendation_score')->default(0);
            $table->string('external_id', 100)->nullable()->index();
            $table->boolean('is_featured')->default(false);
            $table->timestamps();

            $table->index(['category_id', 'availability']);
            $table->index(['brand_id', 'product_range']);
            $table->index('price');
        });

        Schema::create('product_skin_concerns', function (Blueprint $table): void {
            $table->foreignId('product_id')->constrained()->cascadeOnDelete();
            $table->foreignId('skin_concern_id')->constrained()->cascadeOnDelete();
            $table->primary(['product_id', 'skin_concern_id']);
        });

        Schema::create('product_reviews', function (Blueprint $table): void {
            $table->id();
            $table->foreignId('product_id')->constrained()->cascadeOnDelete();
            $table->foreignId('user_id')->constrained()->cascadeOnDelete();
            $table->unsignedTinyInteger('rating');
            $table->string('title', 150)->nullable();
            $table->text('body')->nullable();
            $table->boolean('is_verified_purchase')->default(false);
            $table->timestamps();

            $table->unique(['product_id', 'user_id']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('product_reviews');
        Schema::dropIfExists('product_skin_concerns');
        Schema::dropIfExists('products');
        Schema::dropIfExists('subcategories');
        Schema::dropIfExists('categories');
        Schema::dropIfExists('brands');
    }
};
