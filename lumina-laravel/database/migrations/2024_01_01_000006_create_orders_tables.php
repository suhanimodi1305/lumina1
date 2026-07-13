<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up(): void
    {
        Schema::create('orders', function (Blueprint $table): void {
            $table->id();
            $table->string('order_id', 30)->unique();
            $table->string('tracking_id', 20)->unique();
            $table->foreignId('user_id')->nullable()->constrained()->nullOnDelete();
            $table->string('full_name', 150);
            $table->string('phone', 15);
            $table->string('email')->nullable();
            $table->string('address_line1', 250);
            $table->string('address_line2', 250)->nullable();
            $table->string('city', 100);
            $table->string('state', 100);
            $table->string('pincode', 10);
            $table->enum('payment_method', ['cod', 'upi', 'card', 'netbanking', 'wallet'])->default('cod');
            $table->string('payment_status', 20)->default('pending');
            $table->enum('status', ['pending', 'confirmed', 'packed', 'shipped', 'out_for_delivery', 'delivered', 'cancelled', 'returned'])->default('pending');
            $table->decimal('subtotal', 10, 2)->default(0);
            $table->decimal('delivery_charge', 8, 2)->default(0);
            $table->decimal('discount', 8, 2)->default(0);
            $table->decimal('total', 10, 2)->default(0);
            $table->date('estimated_delivery')->nullable();
            $table->timestamp('delivered_at')->nullable();
            $table->text('order_notes')->nullable();
            $table->timestamps();

            $table->index(['user_id', 'created_at']);
            $table->index('status');
        });

        Schema::create('order_items', function (Blueprint $table): void {
            $table->id();
            $table->foreignId('order_id')->constrained()->cascadeOnDelete();
            $table->foreignId('product_id')->nullable()->constrained()->nullOnDelete();
            $table->string('name', 200);
            $table->string('brand', 100)->nullable();
            $table->string('image_url')->nullable();
            $table->string('sku', 50)->nullable();
            $table->string('shade', 100)->nullable();
            $table->decimal('price', 10, 2);
            $table->unsignedSmallInteger('quantity')->default(1);
        });

        Schema::create('order_status_logs', function (Blueprint $table): void {
            $table->id();
            $table->foreignId('order_id')->constrained()->cascadeOnDelete();
            $table->string('status', 25);
            $table->string('message', 300);
            $table->string('location', 200)->nullable();
            $table->timestamp('created_at')->useCurrent();

            $table->index(['order_id', 'created_at']);
        });

        Schema::create('user_requirements', function (Blueprint $table): void {
            $table->id();
            $table->string('req_id', 30)->unique();
            $table->foreignId('user_id')->constrained()->cascadeOnDelete();
            $table->string('title', 200);
            $table->text('custom_product')->nullable();
            $table->text('requirement_notes')->nullable();
            $table->unsignedSmallInteger('quantity')->default(1);
            $table->enum('priority', ['low', 'normal', 'high', 'urgent'])->default('normal');
            $table->string('full_name', 150);
            $table->string('phone', 15);
            $table->string('email')->nullable();
            $table->string('address_line1', 250);
            $table->string('address_line2', 250)->nullable();
            $table->string('city', 100);
            $table->string('state', 100);
            $table->string('pincode', 10);
            $table->enum('status', ['pending', 'accepted', 'processing', 'dispatched', 'delivered', 'rejected', 'cancelled'])->default('pending');
            $table->foreignId('assigned_to')->nullable()->constrained('users')->nullOnDelete();
            $table->text('employee_notes')->nullable();
            $table->foreignId('linked_order_id')->nullable()->constrained('orders')->nullOnDelete();
            $table->timestamps();
        });

        Schema::create('user_requirements_products', function (Blueprint $table): void {
            $table->foreignId('user_requirement_id')->constrained('user_requirements')->cascadeOnDelete();
            $table->foreignId('product_id')->constrained()->cascadeOnDelete();
            $table->primary(['user_requirement_id', 'product_id']);
        });
    }

    public function down(): void
    {
        Schema::dropIfExists('user_requirements_products');
        Schema::dropIfExists('user_requirements');
        Schema::dropIfExists('order_status_logs');
        Schema::dropIfExists('order_items');
        Schema::dropIfExists('orders');
    }
};
