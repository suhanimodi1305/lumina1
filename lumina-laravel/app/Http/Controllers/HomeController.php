<?php

namespace App\Http\Controllers;

use App\Models\Banner;
use App\Models\Category;
use App\Models\Product;
use Illuminate\Http\Request;
use Illuminate\View\View;

class HomeController extends Controller
{
    public function index(Request $request): View
    {
        $heroBanners = Banner::where('position', 'home_hero')
            ->where('is_active', true)
            ->orderBy('sort_order')
            ->get();

        $featuredProducts = Product::with(['brand', 'category'])
            ->featured()
            ->inStock()
            ->limit(8)
            ->get();

        $categories = Category::where('is_active', true)
            ->orderBy('sort_order')
            ->get();

        return view('home', compact('heroBanners', 'featuredProducts', 'categories'));
    }
}
