<?php

namespace App\Services;

use App\Models\Brand;
use App\Models\Category;
use App\Models\Product;
use Illuminate\Support\Facades\Cache;
use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Log;
use Illuminate\Support\Str;

class MakeupApiSyncService
{
    private string $apiUrl;
    private bool   $enabled;

    public function __construct()
    {
        $this->apiUrl  = env('MAKEUP_API_URL', 'https://makeup-api.herokuapp.com/api/v1/products.json');
        $this->enabled = (bool) env('MAKEUP_API_ENABLED', true);
    }

    /**
     * Run a full or filtered sync from the Makeup API.
     * Fallback: if API is unavailable, logs and returns gracefully — app continues normally.
     */
    public function sync(?string $category = null): array
    {
        $result = ['created' => 0, 'updated' => 0, 'skipped' => 0, 'errors' => 0, 'total_api' => 0];

        if (!$this->enabled) {
            Log::info('MakeupApiSync: disabled via MAKEUP_API_ENABLED=false');
            return $result;
        }

        try {
            $params = [];
            if ($category) {
                $params['product_type'] = $category;
            }

            $response = Http::timeout(30)->get($this->apiUrl, $params);

            if (!$response->successful()) {
                Log::warning('MakeupApiSync: API returned ' . $response->status());
                return $result;
            }

            $products = $response->json();
            if (!is_array($products)) {
                Log::warning('MakeupApiSync: unexpected response format');
                return $result;
            }

            $result['total_api'] = count($products);

            foreach ($products as $apiProduct) {
                try {
                    $outcome = $this->upsertProduct($apiProduct);
                    $result[$outcome]++;
                } catch (\Throwable $e) {
                    $result['errors']++;
                    Log::warning('MakeupApiSync: product upsert failed', [
                        'id'      => $apiProduct['id'] ?? null,
                        'name'    => $apiProduct['name'] ?? null,
                        'error'   => $e->getMessage(),
                    ]);
                }
            }

            // Invalidate product cache
            Cache::tags(['products'])->flush();

            Log::info('MakeupApiSync complete', $result);

        } catch (\Throwable $e) {
            // FALLBACK: API is unavailable — log and return gracefully
            Log::error('MakeupApiSync: API unavailable — ' . $e->getMessage());
        }

        return $result;
    }

    public function upsertProduct(array $api): string
    {
        $name  = trim($api['name'] ?? '');
        $brand = trim($api['brand'] ?? '');

        if (empty($name)) {
            return 'skipped';
        }

        // Duplicate detection: by external_id or name+brand combo
        $existing = null;
        if (!empty($api['id'])) {
            $existing = Product::where('external_id', (string) $api['id'])->first();
        }
        if (!$existing && $brand) {
            $existing = Product::whereRaw('LOWER(name) = ?', [strtolower($name)])
                ->whereHas('brand', fn ($q) => $q->whereRaw('LOWER(name) = ?', [strtolower($brand)]))
                ->first();
        }

        // Resolve / create brand
        $brandModel = Brand::firstOrCreate(
            ['slug' => Str::slug($brand ?: 'unknown')],
            ['name' => $brand ?: 'Unknown', 'slug' => Str::slug($brand ?: 'unknown'), 'is_active' => true]
        );

        // Resolve category (makeup)
        $category = Category::where('type', 'makeup')->first();

        $data = [
            'brand_id'           => $brandModel->id,
            'category_id'        => $category?->id ?? 1,
            'name'               => $name,
            'slug'               => Str::slug($name . '-' . ($api['id'] ?? Str::random(6))),
            'sku'                => 'API-' . ($api['id'] ?? Str::random(8)),
            'product_range'      => 'makeup',
            'description'        => $api['description'] ?? '',
            'key_ingredients'    => '',
            'price'              => $this->parsePrice($api['price'] ?? null),
            'image_url'          => $api['api_featured_image'] ?? '',
            'rating'             => $this->parseRating($api['rating'] ?? null),
            'reviews_count'      => (int) ($api['product_tags'] ? count($api['product_tags'] ?? []) : 0),
            'availability'       => 'in_stock',
            'external_id'        => (string) ($api['id'] ?? ''),
            'is_featured'        => false,
        ];

        if ($existing) {
            $existing->update($data);
            return 'updated';
        }

        Product::create($data);
        return 'created';
    }

    private function parsePrice(?string $price): ?float
    {
        if (empty($price)) return null;
        $cleaned = preg_replace('/[^\d.]/', '', $price);
        return $cleaned ? (float) $cleaned : null;
    }

    private function parseRating(mixed $rating): float
    {
        if (empty($rating)) return 0.0;
        $val = (float) $rating;
        return min(5.0, max(0.0, $val));
    }
}
