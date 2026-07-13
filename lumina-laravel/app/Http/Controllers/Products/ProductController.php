<?php

namespace App\Http\Controllers\Products;

use App\Http\Controllers\Controller;
use App\Models\Brand;
use App\Models\Category;
use App\Models\Product;
use App\Models\SkinConcern;
use App\Services\MembershipService;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Cache;
use Illuminate\View\View;

class ProductController extends Controller
{
    public function __construct(private MembershipService $membershipService) {}

    public function index(Request $request): View
    {
        $cacheKey = 'products.' . md5($request->fullUrl()) . '.' . ($request->user()?->id ?? 'guest');

        $data = Cache::tags(['products'])->remember($cacheKey, 600, function () use ($request) {
            $query = Product::with(['brand', 'category'])
                ->inStock();

            // Tier price ceiling for authenticated users
            if ($request->user()) {
                $tier         = $this->membershipService->getEffectiveTier($request->user());
                $priceCeiling = $this->membershipService->getPriceCeiling($tier);
                $query->withinPriceCap($priceCeiling);
            }

            // Filters
            if ($category = $request->query('category')) {
                $query->whereHas('category', fn ($q) => $q->where('slug', $category));
            }
            if ($brand = $request->query('brand')) {
                $query->whereHas('brand', fn ($q) => $q->where('slug', $brand));
            }
            if ($skinType = $request->query('skin_type')) {
                $query->whereJsonContains('suitable_for_skin_types', $skinType);
            }
            if ($concern = $request->query('concern')) {
                $query->whereHas('skinConcerns', fn ($q) => $q->where('slug', $concern));
            }
            if ($range = $request->query('range')) {
                $query->where('product_range', $range);
            }
            if ($search = $request->query('search')) {
                $query->where(fn ($q) => $q
                    ->where('name', 'like', "%{$search}%")
                    ->orWhere('description', 'like', "%{$search}%")
                    ->orWhereHas('brand', fn ($b) => $b->where('name', 'like', "%{$search}%"))
                );
            }

            return $query->orderByDesc('ai_recommendation_score')->paginate(16)->withQueryString();
        });

        $categories   = Cache::remember('categories.active', 3600, fn () => Category::where('is_active', true)->orderBy('sort_order')->get());
        $brands       = Cache::remember('brands.active', 3600, fn () => Brand::where('is_active', true)->orderBy('name')->get());
        $skinConcerns = Cache::remember('skin_concerns.all', 3600, fn () => SkinConcern::orderBy('name')->get());

        return view('products.index', [
            'products'     => $data,
            'categories'   => $categories,
            'brands'       => $brands,
            'skinConcerns' => $skinConcerns,
            'filters'      => $request->only(['category', 'brand', 'skin_type', 'concern', 'range', 'search']),
        ]);
    }

    public function show(Request $request, Product $product): View
    {
        $product->load(['brand', 'category', 'subcategory', 'skinConcerns', 'reviews.user']);

        $related = Product::with('brand')
            ->where('category_id', $product->category_id)
            ->where('id', '!=', $product->id)
            ->inStock()
            ->limit(4)
            ->get();

        $userReview = null;
        if ($request->user()) {
            $userReview = $product->reviews()->where('user_id', $request->user()->id)->first();
        }

        return view('products.show', compact('product', 'related', 'userReview'));
    }
}
